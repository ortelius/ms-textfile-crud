# Copyright (c) 2021 Linux Foundation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import base64
import json
import logging
import os
import socket
from http import HTTPStatus
from time import sleep
from typing import List, Optional

import psycopg2
import psycopg2.extras
import requests
import uvicorn
import yaml
from fastapi import (FastAPI, HTTPException, Query, Request, Response,
                     responses, status)
from pydantic import BaseModel, Field
from sqlalchemy import sql, create_engine
from sqlalchemy.exc import InterfaceError, OperationalError, StatementError

# Init Globals
service_name = 'ortelius-ms-textfile-crud'
db_conn_retry = 3

# Init FastAPI
app = FastAPI(
    title=service_name,
    description="TextFile Crud APIs",
    version="1.0.0",
    terms_of_service="http://swagger.io/terms/",
    contact={
        "email": "notifysupport@deployhub.com",
    },
    license_info={
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
    },)

# Init db connection
db_host = os.getenv("DB_HOST", "localhost")
db_name = os.getenv("DB_NAME", "postgres")
db_user = os.getenv("DB_USER", "postgres")
db_pass = os.getenv("DB_PASS", "postgres")
db_port = os.getenv("DB_PORT", "5432")
validateuser_url = os.getenv('VALIDATEUSER_URL', None )

if (validateuser_url is None):
    validateuser_host = os.getenv('MS_VALIDATE_USER_SERVICE_HOST', '127.0.0.1')
    host = socket.gethostbyaddr(validateuser_host)[0]
    validateuser_url = 'http://' + host + ':' + str(os.getenv('MS_VALIDATE_USER_SERVICE_PORT', 80))

engine = create_engine("postgresql+psycopg2://" + db_user + ":" + db_pass + "@" + db_host + ":" + db_port + "/" + db_name, pool_pre_ping=True)

# health check endpoint
class StatusMsg(BaseModel):
    status: str
    service_name: Optional[str] = None


@app.get("/health")
async def health(response: Response) -> StatusMsg:
    try:
        with engine.connect() as connection:
            conn = connection.connection
            cursor = conn.cursor()
            cursor.execute('SELECT 1')
            if cursor.rowcount > 0:
                return {"status": 'UP', "service_name": service_name}
            response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
            return {"status": 'DOWN'}

    except Exception as err:
        print(str(err))
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": 'DOWN'}
# end health check

def get_mimetype(filetype, dstr):
    if (filetype.lower() == 'readme'):
        return 'text/markdown'
    try:
        json.loads(dstr)
        return 'application/json'
    except:
        pass

    try:
        yaml.safe_load(dstr)
        return 'text/yaml'
    except:
        pass

    return 'text/plain'


class Message(BaseModel):
    detail: str


@app.get('/msapi/textfile')
async def getFileContent(request: Request, response: Response, compid: int = Query(..., ge=1), filetype: str = Query(..., regex="^(?!\s*$).+")):
    try:
        result = requests.get(validateuser_url + "/msapi/validateuser", cookies=request.cookies)
        if (result is None):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization Failed")

        if (result.status_code != status.HTTP_200_OK):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization Failed status_code=" + str(result.status_code))
    except Exception as err:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization Failed:" + str(err)) from None

    try:
        #Retry logic for failed query
        no_of_retry = db_conn_retry
        attempt = 1;
        while True:
            try:
                with engine.connect() as connection:
                    conn = connection.connection

                    if (filetype is None and 'swagger' in request.path_params):
                        filetype = 'swagger'

                    cursor = conn.cursor()
                    sqlstmt = 'SELECT * FROM dm.dm_textfile WHERE compid = %s AND filetype = %s Order by lineno'
                    cursor.execute(sqlstmt, [compid, filetype])
                    records = cursor.fetchall()
                    cursor.close()
                    conn.commit()

                    file = []
                    for rec in records:
                        file.append(rec[3])

                    encoded_str = "".join(file)
                    decoded_str = base64.b64decode(encoded_str).decode("utf-8")
                    return Response(content=decoded_str, media_type=get_mimetype(filetype, decoded_str))

            except (InterfaceError, OperationalError) as ex:
                if attempt < no_of_retry:
                    sleep_for = 0.2
                    logging.error(
                        "Database connection error: {} - sleeping for {}s"
                        " and will retry (attempt #{} of {})".format(
                            ex, sleep_for, attempt, no_of_retry
                        )
                    )
                    #200ms of sleep time in cons. retry calls
                    sleep(sleep_for)
                    attempt += 1
                    continue
                else:
                    raise

    except HTTPException:
        raise
    except Exception as err:
        print(str(err))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(err)) from None


class FileRequest(BaseModel):
    compid: int = Field(..., ge=1)
    filetype: str = Field(..., regex="^(?!\s*$).+")
    file: List[str]


@app.post('/msapi/textfile')
async def saveFileContent(request: Request, fileRequest: FileRequest):
    try:
        result = requests.get(validateuser_url + "/msapi/validateuser", cookies=request.cookies)
        if (result is None):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization Failed")

        if (result.status_code != status.HTTP_200_OK):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization Failed status_code=" + str(result.status_code))
    except Exception as err:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization Failed:" + str(err)) from None

    try:

        #Retry logic for failed query
        no_of_retry = db_conn_retry
        attempt = 1;
        while True:
            try:
                with engine.connect() as connection:
                    conn = connection.connection

                    line_no = 1
                    data_list = []
                    for line in fileRequest.file:
                        d = (fileRequest.compid, fileRequest.filetype, line_no, line)
                        line_no += 1
                        data_list.append(d)

                    cursor = conn.cursor()
                    # pre-processing
                    pre_process = 'DELETE FROM dm.dm_textfile WHERE compid = %s AND filetype = %s;'
                    cursor.execute(pre_process, [fileRequest.compid, fileRequest.filetype])

                    if len(data_list) > 0:
                        records_list_template = ','.join(['%s'] * len(data_list))
                        sqlstmt = 'INSERT INTO dm.dm_textfile(compid, filetype, lineno, base64str) VALUES {}'.format(records_list_template)
                        cursor.execute(sqlstmt, data_list)

                    cursor.close()
                    conn.commit()

                    return Message(detail='components updated succesfully')

            except (InterfaceError, OperationalError) as ex:
                if attempt < no_of_retry:
                    sleep_for = 0.2
                    logging.error(
                        "Database connection error: {} - sleeping for {}s"
                        " and will retry (attempt #{} of {})".format(
                            ex, sleep_for, attempt, no_of_retry
                        )
                    )
                    #200ms of sleep time in cons. retry calls
                    sleep(sleep_for)
                    attempt += 1
                    continue
                else:
                    raise

    except HTTPException:
        raise
    except Exception as err:
        print(str(err))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(err)) from None

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5002)

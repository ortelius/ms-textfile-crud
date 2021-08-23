import os
import json
import yaml
import base64

import psycopg2
import pybreaker
from flask import Flask, request, make_response 
from flask_restful import Api, Resource
from flask_swagger_ui import get_swaggerui_blueprint

# Initialize flask
app = Flask(__name__)
api = Api(app)
app.url_map.strict_slashes = False

### swagger specific ###
SWAGGER_URL = '/swagger'
API_URL = '/static/swagger-ui/doc/swagger.yml'
SWAGGERUI_BLUEPRINT = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': "ortelius-ms-textfile-crud"
    }
)
app.register_blueprint(SWAGGERUI_BLUEPRINT, url_prefix=SWAGGER_URL)
### end swagger specific ###

# Initialize database connection
db_host = os.getenv("DB_HOST", "localhost")
db_name = os.getenv("DB_NAME", "postgres")
db_user = os.getenv("DB_USER", "postgres")
db_pass = os.getenv("DB_PASS", "postgres")
db_port = os.getenv("DB_PORT", "5432")
validateuser_url = os.getenv("VALIDATEUSER_URL", "http://localhost:5000")

conn_circuit_breaker = pybreaker.CircuitBreaker(
    fail_max=1,
    reset_timeout=10,
)

@conn_circuit_breaker
def create_conn():
    conn = psycopg2.connect(host=db_host, database=db_name, user=db_user, password=db_pass, port=db_port)
    return conn

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

class ComponentTextfile(Resource):
    def post(cls):
        
        result = requests.get(validateuser_url + "/msapi/validateuser", cookies=request.cookies)
        if (result is None):
            return None, 404

        if (result.status_code != 200):
            return result.json(), 404
        
        try: 
            input_data = request.get_json()
            
            file = input_data.get('file', '')
            compid = input_data.get('compid', -1)
            filetype = input_data.get('filetype', '')
            
            line_no = 1
            data_list = []
            for line in file:
                d = (compid, filetype, line_no, line)
                line_no += 1
                data_list.append(d)
    
            conn = create_conn()
            cursor = conn.cursor()
            #pre-processing
            pre_process = 'DELETE FROM dm.dm_textfile WHERE compid = %s AND filetype = %s;'
            cursor.execute(pre_process, [compid, filetype])
            
            if len(data_list) > 0:
                records_list_template = ','.join(['%s'] * len(data_list))
                sql = 'INSERT INTO dm.dm_textfile(compid, filetype, lineno, base64str) VALUES {}'.format(records_list_template)
                cursor.execute(sql, data_list)
    
            conn.commit()   # commit the changes
            cursor.close()
            
            return ({"message": f'components updated Succesfully'})
    
        except Exception as err:
            print(err)
            conn = create_conn()
            cursor = conn.cursor()
            cursor.execute("ROLLBACK")
            conn.commit()
            
            return ({"message": f'oops!, Something went wrong!'})
    
    def get(cls):
        
        result = requests.get(validateuser_url + "/msapi/validateuser", cookies=request.cookies)
        if (result is None):
            return None, 404

        if (result.status_code != 200):
            return result.json(), 404
        
        try: 
            compid = request.args.get('compid')
            filetype = request.args.get('filetype', None)
            
            if (filetype is None and 'swagger' in request.path):
               filetype = 'swagger'
            
            conn = create_conn()
            cursor = conn.cursor()
            sql = 'SELECT * FROM dm.dm_textfile WHERE compid = %s AND filetype = %s Order by lineno'
            cursor.execute(sql, [compid, filetype])
            records = cursor.fetchall()
            
            file = []
            for rec in records:
                file.append(rec[3])
                 
            # print (file) 
            conn.commit()   # commit the changes
            cursor.close()
            encoded_str = "".join(file)
            decoded_str = base64.b64decode(encoded_str).decode("utf-8")
            response = make_response(decoded_str)   
            response.headers['Content-Type'] = get_mimetype(filetype, decoded_str) + '; charset=utf-8'            
            return response
    
        except Exception as err:
            print(err)
            conn = create_conn()
            cursor = conn.cursor()
            cursor.execute("ROLLBACK")
            conn.commit()
            
            return ({"message": f'oops!, Something went wrong!'})

  
##
# Actually setup the Api resource routing here
##
api.add_resource(ComponentTextfile, '/msapi/textfile/')
  
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5002)

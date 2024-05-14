# ortelius-ms-textfile-crud
![Release](https://img.shields.io/github/v/release/ortelius/ms-textfile-crud?sort=semver)
![license](https://img.shields.io/github/license/ortelius/.github)

![Build](https://img.shields.io/github/actions/workflow/status/ortelius/ms-textfile-crud/build-push-chart.yml)
[![MegaLinter](https://github.com/ortelius/ms-textfile-crud/workflows/MegaLinter/badge.svg?branch=main)](https://github.com/ortelius/ms-textfile-crud/actions?query=workflow%3AMegaLinter+branch%3Amain)
![CodeQL](https://github.com/ortelius/ms-textfile-crud/workflows/CodeQL/badge.svg)
[![OpenSSF
-Scorecard](https://api.securityscorecards.dev/projects/github.com/ortelius/ms-textfile-crud/badge)](https://api.securityscorecards.dev/projects/github.com/ortelius/ms-textfile-crud)

![Discord](https://img.shields.io/discord/722468819091849316)

> Version 10.0.0

RestAPI endpoint for retrieving SBOM data to a component

## Path Table

| Method | Path | Description |
| --- | --- | --- |
| GET | [/health](#gethealth) | Health |
| GET | [/msapi/textfile](#getmsapitextfile) | Get File Content |
| POST | [/msapi/textfile](#postmsapitextfile) | Save File Content |

## Reference Table

| Name | Path | Description |
| --- | --- | --- |
| FileRequest | [#/components/schemas/FileRequest](#componentsschemasfilerequest) |  |
| HTTPValidationError | [#/components/schemas/HTTPValidationError](#componentsschemashttpvalidationerror) |  |
| StatusMsg | [#/components/schemas/StatusMsg](#componentsschemasstatusmsg) |  |
| ValidationError | [#/components/schemas/ValidationError](#componentsschemasvalidationerror) |  |

## Path Details

***

### [GET]/health

- Summary  
Health

- Description  
This health check end point used by Kubernetes

#### Responses

- 200 Successful Response

`application/json`

```ts
{
  status?: string
  service_name?: string
}
```

***

### [GET]/msapi/textfile

- Summary  
Get File Content

#### Parameters(Query)

```ts
compid: integer
```

```ts
filetype?: Partial(string) & Partial(null)
```

#### Responses

- 200 Successful Response

`application/json`

```ts
{}
```

- 422 Validation Error

`application/json`

```ts
{
  detail: {
    loc?: Partial(string) & Partial(integer)[]
    msg: string
    type: string
  }[]
}
```

***

### [POST]/msapi/textfile

- Summary  
Save File Content

#### RequestBody

- application/json

```ts
{
  compid?: integer
  filetype?: string
  file?: string[]
}
```

#### Responses

- 200 Successful Response

`application/json`

```ts
{}
```

- 422 Validation Error

`application/json`

```ts
{
  detail: {
    loc?: Partial(string) & Partial(integer)[]
    msg: string
    type: string
  }[]
}
```

## References

### #/components/schemas/FileRequest

```ts
{
  compid?: integer
  filetype?: string
  file?: string[]
}
```

### #/components/schemas/HTTPValidationError

```ts
{
  detail: {
    loc?: Partial(string) & Partial(integer)[]
    msg: string
    type: string
  }[]
}
```

### #/components/schemas/StatusMsg

```ts
{
  status?: string
  service_name?: string
}
```

### #/components/schemas/ValidationError

```ts
{
  loc?: Partial(string) & Partial(integer)[]
  msg: string
  type: string
}
```

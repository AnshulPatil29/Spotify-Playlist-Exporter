# Authorization Control Flow

This is an older version of the code which required the use of  `CLIENT_SECRET` to be packaged with the code to be used. 

The current version uses PKCE (Proof Key for Code Exchange)

- requires a `config.json` file with structure
```json
{
    "SPOTIFY":{
        "CLIENT_ID":"client-id",
        "CLIENT_SECRET":"client-secret",
        "REDIRECT_URI":"http://127.0.0.1:8888/callback"
    }
}
```
- and the user needs to go to the spotify dev dashboard, create an app and use the CLIENT_ID, SECRET and REDIRECT_URI from there

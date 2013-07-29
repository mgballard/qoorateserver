# our general app settings
app = {
    # Verbose debugging?
    "DEBUG_MODE": True,

    ## Temporary directory
    ## no trailing slash
    "TEMP_DIR": "tmp",
    
    ## our service connection parameters
    "SERVICE_INFO": {
        "SERVICE_REGISTRATION_PASSPHRASE": "137b789e-b7eb-475a-8d5a-b16ab544yurp", 
        "SERVICE_ID": "uploader",
        "SERVICE_REGISTRATION_ADDR": "ipc://run/uploader/brubeck_svc_registration",
        "SERVICE_PASSPHRASE": "137b789e-b7eb-475a-8d5a-b16ab544yurp",
        "SERVICE_ADDR": "ipc://run/uploader/brubeck_svc",
        "SERVICE_RESPONSE_ADDR": "ipc://run/uploader/brubeck_svc_response",
        #"SERVICE_HEARTBEAT_ADDR": "ipc://run/uploader/brubeck_svc_heartbeat",
    },
}

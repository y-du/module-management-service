### /modules

**GET**

_List all installed modules._

    Response media type: application/json
    
    {
      <string>: {
        "name": <string>,
        "description": <string>,
        "services": {
          <string>: {"hash": <string>}
        },
        "hash": <string>,
        "state": <string>           # "active", "inactive"
      },
      ...
    }

**POST**

_Install / update module. Saves module metadata locally and configs to Configuration Storage Service._

_If updating the module state must be "inactive"._

    Request media type: application/json


    {
      "id": <string>,
      "name": <string>,
      "description": <string>,
      "services": {
        <string>: {
          "deployment_configs": {
            "image": <string>,
            "volumes": {<string>:<string>},                 # can be null
            "devices": {<string>:<string>},                 # can be null
            "ports": [                                      # can be null
              {
                "container": <number>,
                "host": <number>,
                "protocol": <string/Null>                   # "tcp", "udp", "sctp"
              }
            ]
          },
          "service_configs": {<string>:<string/number>},    # can be null
          "hash": <string>
        }
      },
      "hash": <string>
    }


### /modules/{module}

**PATCH**

_Change module state._

_Setting state to "active" triggers deployment (create and start containers)._

_Setting state to "inactive" stops containers._



    Request media type: application/json
    
    {
      "state": <string>         # "active", "inactive"
    }

**DELETE**

_Remove module._

_module must be set to "inactive"._

_Removes metadata, configs, containers, volumes, images._
### /components

**GET**

_List all installed components._

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

_Install / update component. Saves component metadata locally and configs to Configuration Storage Service._

_If updating the component state must be "inactive"._

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


### /components/{component}

**PATCH**

_Change component state._

_Setting state to "active" triggers deployment (create and start containers)._

_Setting state to "inactive" stops containers._



    Request media type: application/json
    
    {
      "state": <string>         # "active", "inactive"
    }

**DELETE**

_Remove component._

_Component must be set to "inactive"._

_Removes metadata, configs, containers, volumes, images._
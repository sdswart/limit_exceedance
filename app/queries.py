data_query = {"Sample":[
        {"$match":{"Equipment":{"$elemMatch":"TargetEquipmentID"}}},
        {"$lookup":
          {"from": "Equipment","localField": "Sensor", "foreignField": "_id", "as": "senor"}},
        {"$unwind": "$sensor"},
        {"$match":{"sensor.Name":{"$elemMatch":{"$regex":"^MetalSCAN.*"}}}},
        {"$project": {"Data":1,"sensor":0}}
      ],
    "Limit":[
      {"$match":{"Equipment":{"$elemMatch":"TargetEquipmentID"}}},
      {"$lookup":
        {"from": "LimitLevel","localField": "Limit", "foreignField": "_id", "as": "levels"}},
      {"$unwind": "$levels"},
      ]
    }

equipment_query = [{"$lookup":
            {"from": "EquipmentBuild","localField": "build_id", "foreignField": "_id", "as": "build"}},
        {"$unwind": "$build"},
        {"$match":{"build.Name":"WT Gearbox"}},
        {"$lookup":
            {"from": "Equipment",
            "let": {"sensors": "$Sensors"},
            "pipeline":[{"$match":{"$_id":{"$in":"$$sensors"}}}],
            "as": "sensor"}},
        {"$unwind": "$sensor"},
        {"$match":{"sensor.Name":{"$regex":"^MetalSCAN.*"}}},
        {"$project": {"_id":1,"build":0,"sensor":0}}
    ]

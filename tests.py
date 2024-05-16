
#
# with open("test", "r", encoding="utf-8") as f:
#    x = f.read()
#
#    g = eval(x)
#
#    print(g)




import json_repair

invalid_json = "{ name: 'John' 'age': 30, 'city': 'New' + ' York', "

fixed_json = json_repair.repair_json(invalid_json)

print(fixed_json)
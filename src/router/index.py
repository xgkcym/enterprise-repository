from langgraph.constants import END

route_list = ["rewrite_query","expand_query","decompose_query",'rag',"abort","finish"]

route_map = {

}

for route in route_list:
    if route == 'finish':
        route_map[route] = END
    elif route == 'abort':
        route_map[route] = END
    else:
        route_map[route] = route
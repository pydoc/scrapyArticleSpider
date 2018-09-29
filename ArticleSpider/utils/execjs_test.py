
import PyV8


# ctxt = PyV8.JSContext()
# ctxt.enter()
# func = ctxt.eval("""
#     (function add(x, y){
#         return x + y;
#         })
# """)
#
# print(func(1, 2))


import execjs


js = execjs.compile("""
    function add(x, y){
        return x + y;
        }
    """)


print(js.call("add", 1, 2))


# server.py

# Assignment 2
# CruzIDs
# Garrett Webb: gswebb
# Kai Hsieh: kahsieh
# Rahul Arora: raarora

#CSE138 Kuper Spring 2021

#acknowledgements
#https://stackabuse.com/serving-files-with-pythons-simplehttpserver-module/
#https://docs.python.org/3/library/http.server.html
#https://stackoverflow.com/questions/31371166/reading-json-from-simplehttpserver-post-data
#https://realpython.com/python-requests/#headers

import requests
import sys
import http.server
import socketserver
import json
from sys import argv
import os
kvstore = {}
main_flag = False
saddr = ""
views = ""
views_list = []

class requestHandler(http.server.BaseHTTPRequestHandler):
    def _set_headers(self, response_code):
        self.send_response(response_code)
        self.send_header("Content-type", "application/json")
        self.end_headers()

    def do_GET(self):
        print("GET REQUEST RECEIVED")

        if "/key-value-store-view" in str(self.path):
            views_list = views.split(",")
            print("key-value-store-view")
            #print("view[0]: http://" + views_list[0] + str(self.path))
            down_instances = []

            for x in views_list:
                try:
                    if x != saddr:
                        r = requests.get('http://' + x + "/key-value-store/check", headers=self.headers)
                        #self._set_headers(r.status_code)
                        #self.wfile.write(r.content)
                except: #
                    down_instances.append(x)
            print("Down Instances:\n")
            print(down_instances)
            
            #for x in views_list:
            #    if x not in down_instances:
            #        for y in down_instances:
            #            r = requests.delete('http://' + x + str(self.path) + "/"+ y, headers=self.headers)
            #            self._set_headers(r.status_code)
            #            self.wfile.write(r.content)

            self._set_headers(response_code=200)
            response = bytes(json.dumps({"message" : "View retrieved successfully", "view" : views }), 'utf-8')

        elif "/key-value-store/" in str(self.path):
                keystr = str(self.path).split("/key-value-store/",1)[1]
                if(len(keystr) > 0 and len(keystr) < 50):
                    if keystr in kvstore:
                        self._set_headers(response_code=200)
                        response = bytes(json.dumps({"doesExist" : True, "message" : "Retrieved successfully", "value" : kvstore[keystr]}), 'utf-8')
                    else:
                        self._set_headers(response_code=404)
                        response = bytes(json.dumps({"doesExist" : False, "error" : "Key does not exist", "message" : "Error in GET"}), 'utf-8')
                elif (len(keystr) > 50):
                    self._set_headers(response_code=400)
                    response = bytes(json.dumps({'error' : "Key is too long", 'message' : "Error in GET"}), 'utf-8')
                elif(len(keystr) == 0):
                    self._set_headers(response_code=400)
                    response = bytes(json.dumps({'error' : "Key not specified", 'message' : "Error in GET"}), 'utf-8')
                self.wfile.write(response)
        
        else:
            #default 500 code to clean up loose ends
            self._set_headers(response_code=500)
        return

    def do_PUT(self):
        if "/key-value-store-view" in str(self.path):
            #in progress
            new_instance = str(self.path).split("://",1)[1] 
            new_instance = new_instance.split('/key')[0]
            # check if formatting is correct
            print("NEW INSTANCE: " + str(new_instance))
            views_list.append(new_instance)

        else:
            if "/key-value-store/" in str(self.path):
                keystr = str(self.path).split("/key-value-store/",1)[1]
                if(len(keystr) > 0 and len(keystr) < 50):
                    self.data_string = self.rfile.read(int(self.headers['Content-Length']))
                    data = json.loads(self.data_string)
                    if "value" not in data:
                        self._set_headers(response_code=400)
                        response = bytes(json.dumps({'error' : "Value is missing", 'message' : "Error in PUT"}), 'utf-8')
                    elif keystr in kvstore:
                        kvstore[keystr] = data["value"]
                        self._set_headers(response_code=200)
                        response = bytes(json.dumps({'message' : "Updated successfully", 'replaced' :True}), 'utf-8')
                    else:
                        kvstore[keystr] = data["value"]
                        self._set_headers(response_code=201)
                        response = bytes(json.dumps({'message' : "Added successfully", 'replaced' :False}), 'utf-8')
                elif (len(keystr) > 50):
                    self._set_headers(response_code=400)
                    response = bytes(json.dumps({'error' : "Key is too long", 'message' : "Error in PUT"}), 'utf-8')
                
                self.wfile.write(response)
            else:
                self._set_headers(response_code=500)
        return
    
    def do_DELETE(self):
        # if (main_flag == False):
        #     try:
        #         r = requests.delete('http://' + saddr + str(self.path), headers=self.headers)
        #         self._set_headers(r.status_code)
        #         self.wfile.write(r.content)
        #     except:
        #         self._set_headers(response_code=503)
        #         response = bytes(json.dumps({"error":"Main instance is down","message":"Error in DELETE"}), 'utf-8')
        #         self.wfile.write(response)
        # else:
        if "/key-value-store-view/" in str(self.path):
            self.data_string = self.rfile.read(int(self.headers['socket-address']))
            data = json.loads(self.data_string)
            view_list.remove(data)
            print("View_list: "view_list)

        if "/key-value-store/" in str(self.path):
            keystr = str(self.path).split("/key-value-store/",1)[1]
            if(len(keystr) > 0 and len(keystr) < 50):
                if keystr in kvstore:
                    del kvstore[keystr]
                    self._set_headers(response_code=200)
                    response = bytes(json.dumps({"doesExist" : True, "message" : "Deleted successfully"}), 'utf-8')
                else:
                    self._set_headers(response_code=404)
                    response = bytes(json.dumps({"doesExist" : False, "error" : "Key does not exist", "message" : "Error in DELETE"}), 'utf-8')
            elif (len(keystr) > 50):
                self._set_headers(response_code=400)
                response = bytes(json.dumps({'error' : "Key is too long", 'message' : "Error in DELETE"}), 'utf-8')
            elif(len(keystr) == 0):
                self._set_headers(response_code=400)
                response = bytes(json.dumps({'error' : "Key not specified", 'message' : "Error in DELETE"}), 'utf-8')
            self.wfile.write(response)
        
        else:
            #default 500 code to clean up loose ends
            self._set_headers(response_code=500)
        return

def run(server_class=http.server.HTTPServer, handler_class=requestHandler, addr='0.0.0.0', port=8085):
    # this function initializes and runs the server on the class defined above
    server_address = (addr, port)
    httpd = server_class(server_address, handler_class)
    print(f"Starting HTTP server on {addr}:{port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.server_close()


if __name__ == '__main__':
    d_ip = ''
    d_port = 8085
    try:
        saddr = os.environ['SOCKET_ADDRESS']
        if len(saddr) > 0:
            print("SOCKET_ADDRESS: " + str(saddr))
        views = os.environ['VIEW']
        if len(saddr) > 0:
            print("VIEWS: " + str(views))

    except:
        print("main instance")
        main_flag = True
        
    print(main_flag)
    x = 0
    for arg in argv:
        print("arg" + str(x) + ": " + str(argv[x]))
        x = x+1

    if len(argv) == 2:
        #call the run function with custom port
        run(port=int(argv[1]))
    else:
        #call the run function with default port 8085
        #addr_s, saddr_port = saddr.split(":")
        run()
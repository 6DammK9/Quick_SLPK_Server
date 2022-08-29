#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
QUICK SLPK SERVER
======================

Minimalist web server engine to publish OGC SceneLayerPackage (.slpk) to Indexed 3d Scene Layer (I3S) web service.

How to use:
- Place .SLPK into a folder (default: "./slpk")
- Configure this script:
	- webserver host
	- webserver port
	- slpk folder
- Launch this script 
- Open browser to "host:port"
- Index page let you access your SLPK as I3S services
-  Also provide an intern viewer for test

How to:
- Configure Index page: modify->  views/services_list.tpl
- Configure Viewer page: modify->  views/carte.tpl


Sources:
- python 2.x
- I3S Specifications: https://github.com/Esri/i3s-spec
- BottlePy 0.13+
- Arcgis Javascript API >=4.6


Autor: RIVIERE Romain
Date: 12/02/2018
Licence: GNU GPLv3 

"""

# Import python modules
import bottlepy.bottle as bottle
from bottlepy.bottle import app, route, run, template, abort, response
from io import BytesIO
import os, sys, json, gzip, zipfile

import mtwsgi

#User parameter
host='localhost'
port=5012
slpkFolder="slpk"
home=os.path.join(os.path.dirname(os.path.realpath(__file__)),slpkFolder) #SLPK Folder
thread_count=4

#https://github.com/RonRothman/mtwsgi/blob/master/mtbottle.py
class MTServer(bottle.ServerAdapter):
    def run(self, handler):
        thread_count = self.options.pop('thread_count', None)
        server = mtwsgi.make_server(self.host, self.port, handler, thread_count, **self.options)
        server.serve_forever()

#*********#
#Functions#
#*********#

#List available SLPK
#slpks=[f for f in os.listdir(home) if os.path.splitext(f)[1].lower()==u".slpk"]

def read(f,slpk):
	"""read gz compressed file from slpk (=zip archive) and output result"""
	if f.startswith("\\"): #remove first \
		f=f[1:]
	with open(os.path.join(home,slpk), 'rb') as file:
		with zipfile.ZipFile(file) as zip:
			if os.path.splitext(f)[1] == ".gz": #unzip GZ
				gz= BytesIO(zip.read(f.replace("\\","/"))) #GZ file  -> convert path sep to zip path sep
				with gzip.GzipFile(fileobj=gz) as gzfile:
					return gzfile.read()
			else:
				return zip.read(f.replace("\\","/")) #Direct read

# the decorator
def enable_cors(fn):
    def _enable_cors(*args, **kwargs):
        # set CORS headers
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Origin, Accept, Content-Type, X-Requested-With, X-CSRF-Token'

        if bottle.request.method != 'OPTIONS':
            # actual request; reply with the actual response
            return fn(*args, **kwargs)

    return _enable_cors

#*********#
#SRIPT****#
#*********#
			
app = app()


@app.route('/')
def list_services():
	#""" List all available SLPK, with LINK to I3S service and Viewer page"""
	#return template('services_list', slpks=slpks)
	IndexJson=dict()
	IndexJson["slpkPath"]=slpkFolder
	response.content_type = 'application/json'
	return json.dumps(IndexJson)
	
@app.route('/<slpk>/SceneServer')
@app.route('/<slpk>/SceneServer/')
@enable_cors
def service_info(slpk):
	try:
		SceneServiceInfo=dict()
		SceneServiceInfo["serviceName"]=slpk
		SceneServiceInfo["name"]=slpk
		SceneServiceInfo["currentVersion"]=10.81
		SceneServiceInfo["serviceVersion"]="1.8"
		SceneServiceInfo["supportedBindings"]=["REST"]
		SceneServiceInfo["layers"] = [json.loads(read("3dSceneLayer.json.gz",slpk))]
		response.content_type = 'application/json'
		return json.dumps(SceneServiceInfo)
	except:
		# Get current system exception
		ex_type, ex_value, ex_traceback = sys.exc_info()
		abort(404, ex_value)
	
@app.route('/<slpk>/SceneServer/layers/0')
@app.route('/<slpk>/SceneServer/layers/0/')
@enable_cors
def layer_info(slpk):
	try:
		SceneLayerInfo=json.loads(read("3dSceneLayer.json.gz",slpk))
		response.content_type = 'application/json'
		return json.dumps(SceneLayerInfo)
	except:
		# Get current system exception
		ex_type, ex_value, ex_traceback = sys.exc_info()
		abort(404, ex_value)

@app.route('/<slpk>/SceneServer/layers/<layer>/sublayers/<sublayer>')
@app.route('/<slpk>/SceneServer/layers/<layer>/sublayers/<sublayer>/')
@enable_cors
def layer_info(slpk,layer,sublayer):
	try:
		SubSceneLayerInfo=json.loads(read("sublayers/%s/3dSceneLayer.json.gz"%sublayer,slpk))
		response.content_type = 'application/json'
		return json.dumps(SubSceneLayerInfo)
	except:
		# Get current system exception
		ex_type, ex_value, ex_traceback = sys.exc_info()
		abort(404, ex_value)

@app.route('/<slpk>/SceneServer/layers/<layer>/sublayers/<sublayer>/nodepages/<nodepage>')
@app.route('/<slpk>/SceneServer/layers/<layer>/sublayers/<sublayer>/nodepages/<nodepage>/')
@enable_cors
def layer_info(slpk,layer,sublayer,nodepage):
	try:
		SubSceneLayerInfo=json.loads(read("sublayers/%s/nodepages/%s.json.gz"%(sublayer,nodepage),slpk))
		response.content_type = 'application/json'
		return json.dumps(SubSceneLayerInfo)
	except:
		# Get current system exception
		ex_type, ex_value, ex_traceback = sys.exc_info()
		abort(404, ex_value)

@app.route('/<slpk>/SceneServer/layers/<layer>/sublayers/<sublayer>/nodes/<node>')
@app.route('/<slpk>/SceneServer/layers/<layer>/sublayers/<sublayer>/nodes/<node>/')
@enable_cors
def node_info(slpk,layer,sublayer,node):
	try:
		NodeIndexDocument=json.loads(read("sublayers/%s/nodes/%s/3dNodeIndexDocument.json.gz"%(sublayer,node),slpk))
		response.content_type = 'application/json'
		return json.dumps(NodeIndexDocument)
	except:
		# Get current system exception
		ex_type, ex_value, ex_traceback = sys.exc_info()
		abort(404, ex_value)

@app.route('/<slpk>/SceneServer/layers/<layer>/sublayers/<sublayer>/nodes/<node>/geometries/<geometry>')
@app.route('/<slpk>/SceneServer/layers/<layer>/sublayers/<sublayer>/nodes/<node>/geometries/<geometry>/')
@enable_cors
def geometry_info(slpk,layer,sublayer,node,geometry):
	try:
		response.content_type = 'application/octet-stream; charset=binary'
		response.content_encoding = 'gzip'
		return read("sublayers/%s/nodes/%s/geometries/%s.bin.gz"%(sublayer,node,geometry),slpk)
	except:
		# Get current system exception
		ex_type, ex_value, ex_traceback = sys.exc_info()
		abort(404, ex_value)

@app.route('/<slpk>/SceneServer/layers/<layer>/sublayers/<sublayer>/nodes/<node>/textures/0_0')
@app.route('/<slpk>/SceneServer/layers/<layer>/sublayers/<sublayer>/nodes/<node>/textures/0_0/')
@enable_cors
def textures_info(slpk,layer,sublayer,node):
	response.headers['Content-Disposition'] = 'attachment; filename="0_0.jpg"'
	response.content_type = 'image/jpeg'
	try:
		return read("sublayers/%s/nodes/%s/textures/0_0.jpg"%(sublayer,node),slpk)
	except:
		try:
			return read("sublayers/%s/nodes/%s/textures/0_0.bin"%(sublayer,node),slpk)
		except:
			# Get current system exception
			ex_type, ex_value, ex_traceback = sys.exc_info()
			abort(404, ex_value)

@app.route('/<slpk>/SceneServer/layers/<layer>/sublayers/<sublayer>/nodes/<node>/textures/0_0_1')
@app.route('/<slpk>/SceneServer/layers/<layer>/sublayers/<sublayer>/nodes/<node>/textures/0_0_1/')
@enable_cors
def Ctextures_info(slpk,layer,sublayer,node):
	try:
		return read("sublayers/%s/nodes/%s/textures/0_0_1.bin.dds.gz"%(sublayer,node),slpk)
	except:
		# Get current system exception
		ex_type, ex_value, ex_traceback = sys.exc_info()
		abort(404, ex_value)

@app.route('/<slpk>/SceneServer/layers/<layer>/sublayers/<sublayer>/nodes/<node>/features/<feature>')
@app.route('/<slpk>/SceneServer/layers/<layer>/sublayers/<sublayer>/nodes/<node>/features/<feature>/')
@enable_cors
def feature_info(slpk,layer,sublayer,node,feature):
	try:
		FeatureData=json.loads(read("sublayers/%s/nodes/%s/features/%s.json.gz"%(sublayer,node,feature),slpk))
		response.content_type = 'application/json'
		return json.dumps(FeatureData)
	except:
		# Get current system exception
		ex_type, ex_value, ex_traceback = sys.exc_info()
		abort(404, ex_value)

@app.route('/<slpk>/SceneServer/layers/<layer>/sublayers/<sublayer>/nodes/<node>/shared')
@app.route('/<slpk>/SceneServer/layers/<layer>/sublayers/<sublayer>/nodes/<node>/shared/')
@enable_cors
def shared_info(slpk,layer,sublayer,node):
	try:
		Sharedressource=json.loads(read("sublayers/%s/nodes/%s/shared/sharedResource.json.gz"%(sublayer,node),slpk))
		response.content_type = 'application/json'
		return json.dumps(Sharedressource)
	except:
		# Get current system exception
		ex_type, ex_value, ex_traceback = sys.exc_info()
		abort(404, ex_value)
		
@app.route('/<slpk>/SceneServer/layers/<layer>/sublayers/<sublayer>/nodes/<node>/attributes/<attribute>/0')
@app.route('/<slpk>/SceneServer/layers/<layer>/sublayers/<sublayer>/nodes/<node>/attributes/<attribute>/0/')
@enable_cors
def attribute_info(slpk,layer,sublayer,node,attribute):
	try:
		return read("sublayers/%s/nodes/%s/attributes/%s/0.bin.gz"%(sublayer,node,attribute),slpk)
	except:
		# Get current system exception
		ex_type, ex_value, ex_traceback = sys.exc_info()
		abort(404, ex_value)

@app.route('/<slpk>/SceneServer/layers/<layer>/nodepages/<nodepage>')
@app.route('/<slpk>/SceneServer/layers/<layer>/nodepages/<nodepage>/')
@enable_cors
def layer_info(slpk,layer,nodepage):
	try:
		SubSceneLayerInfo=json.loads(read("nodepages/0.json.gz",slpk))
		response.content_type = 'application/json'
		return json.dumps(SubSceneLayerInfo)
	except:
		# Get current system exception
		ex_type, ex_value, ex_traceback = sys.exc_info()
		abort(404, ex_value)

@app.route('/<slpk>/SceneServer/layers/<layer>/nodes/<node>')
@app.route('/<slpk>/SceneServer/layers/<layer>/nodes/<node>/')
@enable_cors
def node_info(slpk,layer,node):
	try:
		NodeIndexDocument=json.loads(read("nodes/%s/3dNodeIndexDocument.json.gz"%node,slpk))
		response.content_type = 'application/json'
		return json.dumps(NodeIndexDocument)
	except:
		# Get current system exception
		ex_type, ex_value, ex_traceback = sys.exc_info()
		abort(404, ex_value)

@app.route('/<slpk>/SceneServer/layers/<layer>/nodes/<node>/geometries/0')
@app.route('/<slpk>/SceneServer/layers/<layer>/nodes/<node>/geometries/0/')
@enable_cors
def geometry_info(slpk,layer,node):
	try:
		response.content_type = 'application/octet-stream; charset=binary'
		response.content_encoding = 'gzip'
		return read("nodes/%s/geometries/0.bin.gz"%node,slpk)
	except:
		# Get current system exception
		ex_type, ex_value, ex_traceback = sys.exc_info()
		abort(404, ex_value)

@app.route('/<slpk>/SceneServer/layers/<layer>/nodes/<node>/textures/0_0')
@app.route('/<slpk>/SceneServer/layers/<layer>/nodes/<node>/textures/0_0/')
@enable_cors
def textures_info(slpk,layer,node):
	response.headers['Content-Disposition'] = 'attachment; filename="0_0.jpg"'
	response.content_type = 'image/jpeg'
	try:
		return read("nodes/%s/textures/0_0.jpg"%node,slpk)
	except:
		try:
			return read("nodes/%s/textures/0_0.bin"%node,slpk)
		except:
			# Get current system exception
			ex_type, ex_value, ex_traceback = sys.exc_info()
			abort(404, ex_value)

@app.route('/<slpk>/SceneServer/layers/<layer>/nodes/<node>/textures/0_0_1')
@app.route('/<slpk>/SceneServer/layers/<layer>/nodes/<node>/textures/0_0_1/')
@enable_cors
def Ctextures_info(slpk,layer,node):
	try:
		return read("nodes/%s/textures/0_0_1.bin.dds.gz"%node,slpk)
	except:
		# Get current system exception
		ex_type, ex_value, ex_traceback = sys.exc_info()
		abort(404, ex_value)

@app.route('/<slpk>/SceneServer/layers/<layer>/nodes/<node>/features/0')
@app.route('/<slpk>/SceneServer/layers/<layer>/nodes/<node>/features/0/')
@enable_cors
def feature_info(slpk,layer,node):
	try:
		FeatureData=json.loads(read("nodes/%s/features/0.json.gz"%node,slpk))
		response.content_type = 'application/json'
		return json.dumps(FeatureData)
	except:
		# Get current system exception
		ex_type, ex_value, ex_traceback = sys.exc_info()
		abort(404, ex_value)

@app.route('/<slpk>/SceneServer/layers/<layer>/nodes/<node>/shared')
@app.route('/<slpk>/SceneServer/layers/<layer>/nodes/<node>/shared/')
@enable_cors
def shared_info(slpk,layer,node):
	try:
		Sharedressource=json.loads(read("nodes/%s/shared/sharedResource.json.gz"%node,slpk))
		response.content_type = 'application/json'
		return json.dumps(Sharedressource)
	except:
		# Get current system exception
		ex_type, ex_value, ex_traceback = sys.exc_info()
		abort(404, ex_value)

@app.route('/<slpk>/SceneServer/layers/<layer>/nodes/<node>/attributes/<attribute>/0')
@app.route('/<slpk>/SceneServer/layers/<layer>/nodes/<node>/attributes/<attribute>/0/')
@enable_cors
def attribute_info(slpk,layer,node,attribute):
	try:
		return read("nodes/%s/attributes/%s/0.bin.gz"%(node,attribute),slpk)
	except:
		# Get current system exception
		ex_type, ex_value, ex_traceback = sys.exc_info()
		abort(404, ex_value)

@app.route('/carte/<slpk>')
@enable_cors
def carte(slpk):
	try:
		return template('carte', slpk=slpk, url="http://%s:%s/%s/SceneServer/layers/0"%(host,port,slpk))
	except:
		# Get current system exception
		ex_type, ex_value, ex_traceback = sys.exc_info()
		abort(404, ex_value)

#Run server
#app.run(host=host, port=port)

# Around 10% faster
#https://stackoverflow.com/questions/20824218/how-to-implement-someasyncworker-from-bottle-asynchronous-primer
app.run(server=MTServer, host=host, port=port, thread_count=thread_count)
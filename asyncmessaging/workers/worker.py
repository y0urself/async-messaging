from Celery import xml_request

r = xml_request.delay("weait")
r.ready()
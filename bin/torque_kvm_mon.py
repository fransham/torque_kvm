import time
import json
try:
    import pika
except Exception, e:
    print 'pika library required for ampq not found; monitoring/accounting disabled'
                                    

class DataReporter():
    enable_monitoring = False
    amqp_host = None
    amqp_exchange = None
    amqp_work_queue = None
    
    def __init__(self, config):
        # Load amqp libraries if needed and read related settings from
        # config file.
        if config.has_option("monitoring", "enable_monitoring"):
            self.enable_monitoring = config.getboolean("monitoring", "enable_monitoring")
        self.amqp_host = None
        self.amqp_exchange = None
        if self.enable_monitoring:
            self.amqp_host = config.get("monitoring", "amqp_host")
            self.amqp_exchange = config.get("monitoring", "amqp_exchange")
            self.amqp_work_queue = config.get("monitoring", "amqp_work_queue")
            print 'Configured to broadcast monitoring data to %s exchange on %s, and to work queue %s on %s' % (self.amqp_exchange, self.amqp_host, self.amqp_work_queue, self.amqp_host)
        else:
            print 'monitoring/accounting disabled'


    # Report back some data to the central amqp server.
    def report_data(self, vmuuid, key, value):
        if not self.enable_monitoring:
            return
    
        data = {}
        data['instance_uuid'] = vmuuid
        data['timestamp'] = time.time()
        data['key'] = key
        data['data'] = value

        connection = pika.BlockingConnection(pika.ConnectionParameters(host=self.amqp_host))
        channel = connection.channel()
        
        # Broadcast first
        channel.exchange_declare(exchange=self.amqp_exchange, type='fanout')
        channel.basic_publish(exchange=self.amqp_exchange, routing_key='', body=json.dumps(data))
        
        # Now send to work queue
        channel.queue_declare(queue=self.amqp_work_queue, durable = True)
        channel.basic_publish(exchange='', routing_key=self.amqp_work_queue, body=json.dumps(data), properties = pika.BasicProperties(delivery_mode = 2,))
                                
        connection.close()




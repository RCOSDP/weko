from blinker import NamedSignal
from celery import current_app as current_celery_app
from flask import current_app
from .models import CRISLinkageResult

# make signal
cris_researchmap_linkage_request = NamedSignal('cris_researchmap_linkage_request')

def receiver(item_uuid , **kwargs):
    # This is the function that enqueue into RabbitMQ

    # make Exchange
    exchange = current_app.config.get("LINKAGE_MQ_EXCHANGE")
    # make Queue
    queue = current_app.config.get("LINKAGE_MQ_QUEUE")

    # with Connection('amqp://guest:guest@localhost:5672//') as conn:
    with current_celery_app.pool.acquire(block=True) as conn:

        bound_queue = queue(channel=conn)
        bound_queue.declare()
        bound_exchange = exchange(channel=bound_queue.channel)
        bound_exchange.declare()

        CRISLinkageResult().set_running(item_uuid , 'researchmap')
        
        with conn.Producer(
                conn,
                exchange=bound_exchange,
                routing_key='cris_researchmap_linkage',
                auto_declare=True,
            ) as producer:

            producer.publish(dict(item_uuid=item_uuid), exchange=bound_exchange,routing_key='cris_researchmap_linkage' ,retry=True)


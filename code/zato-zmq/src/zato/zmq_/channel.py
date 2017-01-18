# -*- coding: utf-8 -*-

"""
Copyright (C) 2016 Dariusz Suchojad <dsuch at zato.io>

Licensed under LGPLv3, see LICENSE.txt for terms and conditions.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

# stdlib
from logging import getLogger

# gevent
from gevent import spawn

# Zato
from zato.common import CHANNEL
from zato.common.util import new_cid
from zato.zmq_ import Base
from zato.zmq_.mdp.broker import Broker

# ################################################################################################################################

logger = getLogger(__name__)

# ################################################################################################################################

class Simple(Base):
    """ A ZeroMQ channel other than Majordomo.
    """
    start_in_greenlet = True

    def _start(self):
        super(Simple, self)._start()
        self.init_simple_socket()

        # Micro-optimizations to make things faster
        _spawn = spawn
        _callback = self.on_message_callback
        _new_cid = new_cid
        _service = self.service
        _impl_recv = self.impl.recv
        _config = self.config
        _channel_zmq = CHANNEL.ZMQ

        # Run the main loop
        while self.keep_running:

            # Spawn a new greenlet for the callback invoking a service with data received from the socket on input
            _spawn(_callback, {
                'cid': _new_cid(),
                'service': _service,
                'payload': _impl_recv(), # This line is blocking waiting for requests
                'zato_ctx': {'channel_config': _config}
            }, _channel_zmq, None)

    def _send(self, msg, *args, **kwargs):
        self.impl.send(msg, *args, **kwargs)

# ################################################################################################################################

class MDPv01(Base):
    """ An MDP (Majordomo) v0.1 ZeroMQ channel.
    """
    start_in_greenlet = True

    def _start(self):
        super(MDPv01, self)._start()

        # Run the MDP broker
        self.impl = Broker(self.config, self.on_message_callback)
        self.impl.serve_forever()

# ################################################################################################################################
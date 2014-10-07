#!/usr/bin/env python2.7
# coding: utf-8
import logging
import os
import sys
from logging.config import dictConfig
from multiprocessing import active_children
from time import sleep

from lib.utils import (check_network_status, create_pidfile, daemonize,
                       load_config_from_pyfile, parse_cmd_args, spawn_workers, configuration)
from lib.worker import worker

logger = logging.getLogger('redirect_checker')

keep_running = True


def main_loop_function(config, parent_pid):
    if check_network_status(config.CHECK_URL, config.HTTP_TIMEOUT):
        required_workers_count = config.WORKER_POOL_SIZE - len(
            active_children())
        if required_workers_count > 0:
            logger.info(
                'Spawning {} workers'.format(required_workers_count))
            spawn_workers(
                num=required_workers_count,
                target=worker,
                args=(config,),
                parent_pid=parent_pid
            )
    else:
        logger.critical('Network is down. stopping workers')
        for c in active_children():
            c.terminate()


#def main_loop(config):
#    logger.info(
#        u'Run main loop. Worker pool size={}. Sleep time is {}.'.format(
#            config.WORKER_POOL_SIZE, config.SLEEP
#        ))
#    parent_pid = os.getpid()
#    while True:
#        main_loop_function(config, parent_pid)
#        sleep(config.SLEEP)


def main(argv):
    args = parse_cmd_args(argv[1:])
    config = configuration(args)

    dictConfig(config.LOGGING)
    logger.info(
        u'Run main loop. Worker pool size={}. Sleep time is {}.'.format(
            config.WORKER_POOL_SIZE, config.SLEEP
        ))
    parent_pid = os.getpid()
    while keep_running:
        main_loop_function(config, parent_pid)
        sleep(config.SLEEP)

    return config.EXIT_CODE


if __name__ == '__main__':
    sys.exit(main(sys.argv))

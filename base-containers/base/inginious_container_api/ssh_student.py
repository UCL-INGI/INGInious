# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.
import sys
import inginious_container_api.run_student


# Simply runs run_student with no cmd and ssh set to True
def ssh_student(cmd=None, memory_limit=0, hard_time_limit=0, time_limit=0, container=None, share_network=False, run_as_root=False):

    inginious_container_api.run_student.run_student(cmd=cmd, container=container, time_limit=time_limit,
                hard_time_limit=hard_time_limit, memory_limit=memory_limit,
                share_network=share_network,
                stdin=sys.stdin.fileno(), stdout=sys.stdout.fileno(), stderr=sys.stderr.fileno(),
                signal_handler_callback=inginious_container_api.run_student._hack_signals, ssh=True, run_as_root=run_as_root)

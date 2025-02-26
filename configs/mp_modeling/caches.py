# Copyright (c) 2015 Jason Power
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met: redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer;
# redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution;
# neither the name of the copyright holders nor the names of its
# contributors may be used to endorse or promote products derived from
# this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

""" Caches with options for a simple gem5 configuration script

This file contains L1 I/D and L2 caches to be used in the simple
gem5 configuration script. It uses the SimpleOpts wrapper to set up command
line options from each individual class.
"""

import m5
from m5.objects import (
    Cache,
    IdealPrefetcher,
)

# Add the common scripts to our path
m5.util.addToPath("../../")

from common import SimpleOpts

# Some specific options for caches
# For all options see src/mem/cache/BaseCache.py


class L1Cache(Cache):
    """Simple L1 Cache with default values"""

    assoc = 2
    tag_latency = 2
    data_latency = 2
    response_latency = 2
    mshrs = 4
    tgts_per_mshr = 20

    def __init__(self, options=None):
        super().__init__()
        pass

    def connectBus(self, bus):
        """Connect this cache to a memory-side bus"""
        self.mem_side = bus.cpu_side_ports

    def connectCPU(self, cpu):
        """Connect this cache's port to a CPU-side port
        This must be defined in a subclass"""
        raise NotImplementedError


class L1ICache(L1Cache):
    """Simple L1 instruction cache with default values"""

    # Set the default size
    size = "32kB"
    assoc = 4
    response_latency = 3

    SimpleOpts.add_option(
        "--l1i_size", help=f"L1 instruction cache size. Default: {size}"
    )

    SimpleOpts.add_option(
        "--l1i_assoc",
        help=f"L1 instruction cache associativity. Default: {assoc}",
    )

    SimpleOpts.add_option(
        "--l1i_response_latency",
        help=f"L1 instruction cache response latency. Default: {response_latency}",
    )

    def __init__(self, opts=None):
        super().__init__(opts)
        if opts.l1i_size:
            self.size = opts.l1i_size
        if opts.l1i_assoc:
            self.assoc = opts.l1i_assoc
        if opts.l1i_response_latency:
            self.response_latency = opts.l1i_response_latency

    def connectCPU(self, cpu):
        """Connect this cache's port to a CPU icache port"""
        self.cpu_side = cpu.icache_port


class L1DCache(L1Cache):
    """Simple L1 data cache with default values"""

    # Set the default size
    size = "32kB"
    assoc = 4
    response_latency = 3

    SimpleOpts.add_option(
        "--l1d_size", help=f"L1 data cache size. Default: {size}"
    )

    SimpleOpts.add_option(
        "--l1d_assoc", help=f"L1 data cache associativity. Default: {assoc}"
    )

    SimpleOpts.add_option(
        "--l1d_response_latency",
        help=f"L1 data cache response latency. Default: {response_latency}",
    )

    def __init__(self, opts=None):
        super().__init__(opts)
        if opts.l1d_size:
            self.size = opts.l1d_size
        if opts.l1d_assoc:
            self.assoc = opts.l1d_assoc
        if opts.l1d_response_latency:
            self.response_latency = opts.l1d_response_latency

    def connectCPU(self, cpu):
        """Connect this cache's port to a CPU dcache port"""
        self.cpu_side = cpu.dcache_port


class L2Cache(Cache):
    """Simple L2 Cache with default values"""

    # Default parameters
    size = "1MB"
    assoc = 16
    tag_latency = 20
    data_latency = 20
    response_latency = 12
    mshrs = 20
    tgts_per_mshr = 12
    prefetcher = IdealPrefetcher(
        distance=250, prediction_file="./test/prefetch.txt"
    )

    SimpleOpts.add_option("--l2_size", help=f"L2 cache size. Default: {size}")

    SimpleOpts.add_option(
        "--l2_assoc", help=f"L2 cache associativity. Default: {assoc}"
    )

    SimpleOpts.add_option(
        "--l2_response_latency",
        help=f"L2 cache response latency. Default: {response_latency}",
    )

    def __init__(self, opts=None):
        super().__init__()
        if opts.l2_size:
            self.size = opts.l2_size
        if opts.l2_assoc:
            self.assoc = opts.l2_assoc
        if opts.l2_response_latency:
            self.response_latency = opts.l2_response_latency

    def connectCPUSideBus(self, bus):
        self.cpu_side = bus.mem_side_ports

    def connectMemSideBus(self, bus):
        self.mem_side = bus.cpu_side_ports

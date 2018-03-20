#!/usr/bin/env python2

########################################################################
## This script creates a waterfall plot that updates in real time.
## Copyright (C) 2014 Rachel Domagalski: domagalski@berkeley.edu
##
## This program is free software: you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation, either version 3 of the License, or
## (at your option) any later version.
## ## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program. If not, see <http://www.gnu.org/licenses/>.
########################################################################

import sys
import time
import argparse
import numpy as np
import leuschner as lspec
import numpy.random as npr
import multiprocessing as mp
import matplotlib.pyplot as plt

class SpecDBG(lspec.Spectrometer):
    def check_connected(self):
        pass

    def check_running(self):
        return True

    def init_spec(self):
        pass

    def poll(self):
        time.sleep(0.25)
        self.count += 1

    def read_bram(self, bram):
        noise = npr.randn(self.nchan)
        signal = np.sin(np.pi * np.arange(self.nchan) / self.nchan)
        return 10*signal + noise

    def read_int(self, name):
        return 0

def update_plot(connection, spec, num_integ):

    # Get some initial data to start out with
    plt.ion()
    arr_size = (num_integ, spec.nchan)
    waterfall = np.zeros(arr_size)
    fig = plt.figure()
    ax = plt.gca()
    ax.imshow(waterfall, interpolation='nearest', origin='lower', aspect='auto')
    plt.title('Spectrum')
    plt.xlabel('Channel')
    plt.ylabel('Integration')
    fig.tight_layout()
    fig.canvas.draw()

    # Let's loop this indefinitely for a while, then clean up the code.
    updating = True
    start_chan = 0
    end_chan = spec.nchan
    start_count = spec.count = spec.read_int('acc_num')
    while True:
        # Check for commands to control the plotter.
        if connection.poll():
            command = connection.recv()

            # Channel range
            if command[0] == 'c':
                start_chan, end_chan = map(int, command.split()[1:])
                if start_chan < 0:
                    start_chan = 0
                if end_chan > spec.nchan:
                    end_chan == spec.nchan

            # Change the number of integrations
            if command[0] == 'n':
                num_integ = int(command.split()[1])
                old_integ = arr_size[0]
                if num_integ < old_integ:
                    waterfall = waterfall[:num_integ]
                    arr_size = waterfall.shape
                else:
                    arr_size = (num_integ, spec.nchan)
                    zer_size = (num_integ - old_integ, spec.nchan)
                    waterfall = np.append(waterfall, np.zeros(zer_size))
                    waterfall.resize(arr_size)

            # Reset the plot
            elif command == 'R':
                start_chan = 0
                end_chan = spec.nchan

            # Pause/resume the ploting
            elif command == 'p' or command == 'pause':
                updating = False
            elif command == 'r' or command == 'resume':
                updating = True

        # Update the plot
        new_spec = spec.read_bram(bram_name)
        waterfall = np.append(new_spec, waterfall[:-1]).reshape(arr_size)
        if updating:
            ax.imshow(waterfall[:,start_chan:end_chan],
                      interpolation='nearest', origin='upper', aspect='auto')
            fig.canvas.draw()
        spec.poll()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-a', '--antenna', default='auto0',
                        metavar='input',
                        choices=['auto0', 'auto1', 'cross'],
                        help='Antenna to plot.')
    parser.add_argument('-b', '--bandwidth', type=float, default=12.5e6,
                        help='Bandwidth of the spectrometer.')
    parser.add_argument('-i', '--ip', required=True,
                        help='IP of the ROACH')
    parser.add_argument('-n', '--nyquist', type=int, default=1,
                        help='Nyquist zone of the spectrum')
    parser.add_argument('-N', '--num-integ', type=int, default=500,
                        help='Number of integrations to plot at a time.')
    parser.add_argument('-s', '--spec', default='wide',
                        help='Which spectrometer to use (wide, spec, dbg)')

    args = parser.parse_args()

    # Let's get this party started. :)
    if args.spec == 'wide':
        spec = lspec.Wideband(args.ip)
    elif args.spec == 'spec':
        spec = lspec.Spectrometer(args.ip)
    elif args.spec == 'dbg':
        spec = SpecDBG(args.ip)
    else:
        raise ValueError('Invalid spectrometer mode.')
    spec.check_connected()
    if not spec.check_running():
        spec.init_spec()
    #spec.spec_props(args.bandwidth)

    # Get the bram name to read from
    if 'auto' in args.antenna:
        bram_name = 'spec_' + args.antenna + '_real'
    else:
        print 'Too lazy to do cross-correlation phase...'
        sys.exit()

    # Run the plot updater as a daemon process.
    lock = mp.Lock()
    top, bottom = mp.Pipe()
    update_args = (bottom, spec, args.num_integ)
    plotter = mp.Process(target=update_plot, args=update_args)
    plotter.daemon = True
    plotter.start()

    # Interactive commands
    lock.acquire()
    while True:
        command = raw_input('Enter a command to control the plot: ')
        if command == '':
            continue
        if command == 'q' or command == 'quit':
            break
        elif command == '?':
            print 'Available commands:'
            print 'c <chanels>: Change the range of channels to be plotted.'
            print 'n <npoints>: Change the number of integrations displayed.'
            print 'p / pause:   Pause updates for the plot.'
            print 'q / quit:    Exit the program.'
            print 'r / resume:  Resume updates for the plot.'
            print 'R / reset:   Reset the frequency range.'
        elif command in ['p', 'pause', 'r', 'resume', 'R', 'reset']:
            top.send(command)
        elif command[0] == 'c':
            if len(command.split()) == 3:
                top.send(command)
            else:
                print 'ERROR: Invalid arguments.'
        elif command[0] == 'n':
            if len(command.split()) == 2:
                top.send(command)
            else:
                print 'ERROR: Invalid arguments.'
        else:
            print 'ERROR: Invalid command.'
    lock.release()

#!/usr/bin/env python

import sys
import numpy
import matplotlib.pyplot as plt
import argparse

import frame
import frameProcessor
import db

def main():

    # parse command-line args
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--replay', type=str, default='',
        help = 'name of input data file to replay')

    parser.add_argument('--from-db', action = 'store_true',
        help = 'fetch data from a Mongo database (BROKEN)')
    parser.add_argument('--db-name', type=str, default='TickTock',
        help = 'name of Mongo database to fetch from')
    parser.add_argument('--collection-name', type=str, default='rawdatamodels',
        help = 'name of Mongo collection to fetch from')
    parser.add_argument('--template-collection', type = str, default = 'templatemodels',
        help = 'database collection where spline template should be saved and loaded')
    parser.add_argument('--fetch-limit', type=int, default=100,
        help = 'how many documents to fetch from Mongo database')
    parser.add_argument('--mongo-port', type=int, default=27017,
        help = 'port to use when connecting to a Mongo database')
    parser.add_argument('--batch-replay', action = 'store_true',
        help = 'no interactive prompting for each frame during replay')
    parser.add_argument('--max-frames', type = int, default = 0,
        help = 'maximum number of frames to replay (or no limit if zero)')
    parser.add_argument('--nsamples', type=int, default=0,
        help = 'number of IR ADC samples per frame')
    parser.add_argument('--nsamples-file', type=str, default='../IRLength.txt',
        help = 'number of IR ADC samples per frame')
    parser.add_argument('--adc-tick', type = float, default = 832e-7,
        help = 'ADC sampling period in seconds')
    parser.add_argument('--nfingers', type = int, default = 5,
        help = 'number of fingers on the fiducial bob (')
    parser.add_argument('--length', type = float, default = 1020.,
        help = 'nominal length of pendulum to fiducial marker in milimeters')
    parser.add_argument('--width', type = float, default = 54.,
        help = 'nominal width of the fiducial marker in milimeters')
    parser.add_argument('--show-plots', action = 'store_true',
        help = 'display analysis plots')
    parser.add_argument('--show-centers', action = 'store_true',
        help = 'display center mark on analysis plots')
    parser.add_argument('--show-levels', action = 'store_true',
        help = 'display height mark on analysis plots')
    parser.add_argument('--physical', action = 'store_true',
        help = 'fit frames to a physical model')
    parser.add_argument('--spline', action = 'store_true',
        help = 'fit frames to a spline model')
    parser.add_argument('--save-template', type = str, default = None,
        help = 'filename where spline template should be saved')
    parser.add_argument('--load-template', type = str, default = None,
        help = 'filename of spline template to load and use')
    parser.add_argument('--nspline', type = int, default = 1024,
        help = 'number of spline knots used to build spline template')
    parser.add_argument('--spline-pad', type = float, default = 0.03,
        help = 'amount of padding to use for spline fit region')
    parser.add_argument('--verbose', action = 'store_true',
        help = 'generate verbose output')
    args = parser.parse_args()

    # define tab geometry
    tabs = numpy.array([[-27.,-19.],[-15.,-11.],[-7.,-3.],[3.,7.],[11.,15.],[23.,27.]])

    # get nsamples from nsamples_file
    with open(args.nsamples_file) as f:
        for line in f:
            args.nsamples = int(line)

    # initialize our database connection
    database = db.DB(args)

    # initialize our frame processor
    processor = frameProcessor.FrameProcessor(tabs,args,database)

    # replay a pre-recorded data file if requested
    if args.replay or args.from_db:
        if args.from_db:
            dataTuple = database.loadData()
            data = dataTuple[0]
            timestamp = dataTuple[1]
        elif args.replay:
            # load the input data file
            data = numpy.loadtxt(args.replay)
        if len(data.shape) != 1:
            print 'Data has unexpected shape',data.shape
            return -1
        if args.verbose:
            print 'Read %d bytes from %s' % (len(data),args.replay)
        # loop over data frames
        nframe = len(data)/(1+args.nsamples)

        if args.max_frames == 0 or nframe <= args.max_frames:
            if len(data) % 1+args.nsamples:
                print 'WARNING: Ignoring extra data beyond last frame'
        else:
            print 'Will only replay %d of %d frames' % (args.max_frames,nframe)
            nframe = args.max_frames
        frames = data[:nframe*(1+args.nsamples)].reshape((nframe,1+args.nsamples))
        if args.save_template:
            template = frameProcessor.buildSplineTemplate(frames,args)
            if args.save_template == "db":
                # Save to database as array of ordered pairs (arrays)
                database.saveTemplate(template,timestamp)
            else:
                # Save to file
                numpy.savetxt(args.save_template,template.T)
            if args.show_plots:
                plt.plot(template[0],template[1])
                plt.show()
            return 0
        for i,frame_data in enumerate(frames):
            samplesSinceBoot,samples = frame_data[0],frame_data[1:]
            try:
                period,swing,height = processor.process(samplesSinceBoot,frame.Frame(samples))
                print 'Period = %f secs, swing = %f, height = %f (%d/%d)' % (period,swing,height,i,nframe)
                # check for more recent template
                processor.updateTemplate()
            except RuntimeError,e:
                print str(e)
            if not args.batch_replay:
                response = raw_input('Hit ENTER for next frame, q to quit, b to enter batch mode: ')
                if response == 'q':
                    break
                elif response == 'b':
                    args.batch_replay = True
    else:
        remaining = 0
        samples = numpy.zeros(args.nsamples)
        # read from STDIN to accumulate frames
        while True:
            try:
                line = sys.stdin.readline()
                value = int(line)
                if remaining == 0:
                    samplesSinceBoot = value
                    remaining = args.nsamples
                elif remaining > 0:
                    samples[args.nsamples - remaining] = value
                    remaining -= 1
                    if remaining == 0:
                        period,swing,height = processor.process(samplesSinceBoot,frame.Frame(samples))
                        # period,swing,height = 0,0,500
                        # send the calculated period to our STDOUT and flush the buffer!
                        print period,swing,height
                        sys.stdout.flush()
                        # check for more recent template
                        processor.updateTemplate()
            except Exception,e:
                # Try to keep going silently after any error
                if args.verbose:
                    raise e
                print "Exception: " + str(e) + " " + str(samples)
                sys.stdout.flush()

    # clean up
    processor.finish()

if __name__ == "__main__":
    main()

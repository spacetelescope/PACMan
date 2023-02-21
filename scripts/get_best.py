#!/usr/bin/env python
import pdb
import pickle
import logging
from pylab import *


if __name__ == '__main__':
    logging.info("Proceeding with get_best")
    data = pickle.load(open('JWST_C01_PIs_match_check.pkl', 'rb'))
    outfile = 'JWST_C01_PI_assignments.csv'

    f = open(outfile, 'w')
    f.write('#lastname,firstname,proposid,cs_score\n')
    for item in data.keys():
        tmp = max(data[item][:, 1])
        idx = where(data[item][:, 1] == tmp)[0][0]
        try:
            propid = int(data[item][idx, 0])
        except:
            pdb.set_trace()
        f.write('%s,%d,%.2f\n' % (item, propid, tmp))
    f.close()

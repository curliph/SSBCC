################################################################################
#
# Copyright 2012, Sinclair R.F., Inc.
#
# Utilities required by ssbcc
#
################################################################################

import math

class SSBCCException(Exception):
  def __init__(self,message):
    self.message = message;
  def __str__(self):
    return self.message;

def CeilLog2(v):
  tmp = int(math.log(v,2));
  while 2**tmp < v:
    tmp = tmp + 1;
  return tmp;

def CeilPow2(v):
  return 2**CeilLog2(v);

def IsPowerOf2(v):
  return v == 2**int(math.log(v,2)+0.5);

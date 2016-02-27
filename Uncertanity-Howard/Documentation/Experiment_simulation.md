#Simulation of experimental readings

This document describes the estimation of experimental reading in a time-series data point.

##Background

When observing a steady state data point, the observer collects multiple readings for a period of time that the experimental setup is in steady state and averages the readings to get the observation of a steady state data point. Because of the uncertainty of the sensors and the surroundings, all the readings will differ from each other. This document describes how these readings are estimated.

##Simulation

To simulate the uncertainty of the sensor, an expected value of the reading is needed, and it is assumed that the uncertainty of the sensor is given as a 95% confidence interval under a normal distribution. The standard deviation of the normal distribution is given by

![equation](http://www.sciweavers.org/tex2img.php?eq=%5Csigma%3D%5Cfrac%7Bu_%7Bsensor%7D%7D%7Bz_%7B1-0.95%7D%7D&bc=White&fc=Black&im=png&fs=12&ff=arev&edit=0)

The readings are generated by getting random numbers from a normal distribution with the expected reading as the mean value and the standard deviation estimated from the uncertainty of the sensor.

The number of data points generated to represent the steady state observation depends on the experimental method. The method is defined by the frequency of the data acquistion system and the length of the steady state period, and the number of data points in the steady state observation is given by the product of the frequency and the length of the steady state period.

An example can be given as an experiment of steady-state temperature reading of a 25C medium for 10 minutes with a T-type thermocouple a data acquisition system at 0.1Hz. The expected value is 25C, the uncertainty is 0.5K and the standard deviation is 0.26K. The number of data points in the steady state observation is given by 0.1Hz time 10 time 60 seconds which is 60. The experiment is simulated by getting 60 random numbers from a normal distribution with a mean value at 25C and a standard deviation 0.26K.

##Work to be done

Shall we assume an uncertainty value for environmental noise in the simulation as well?
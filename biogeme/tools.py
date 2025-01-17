"""Implements some useful functions

:author: Michel Bierlaire

:date: Sun Apr 14 10:46:10 2019

"""

# Too constraining
# pylint: disable=invalid-name, too-many-locals

import numpy as np
from scipy.stats import chi2
import biogeme.messaging as msg
import biogeme.exceptions as excep

logger = msg.bioMessage()


def findiff_g(theFunction, x):
    """Calculates the gradient of a function :math`f` using finite differences

    :param theFunction: A function object that takes a vector as an
                        argument, and returns a tuple. The first
                        element of the tuple is the value of the
                        function :math:`f`. The other elements are not
                        used.
    :type theFunction: function

    :param x: argument of the function
    :type x: numpy.array

    :return: numpy vector, same dimension as x, containing the gradient
       calculated by finite differences.
    :rtype: numpy.array

    """
    x = x.astype(float)
    tau = 0.0000001
    n = len(x)
    g = np.zeros(n)
    f = theFunction(x)[0]
    for i in range(n):
        xi = x.item(i)
        xp = x.copy()
        if abs(xi) >= 1:
            s = tau * xi
        elif xi >= 0:
            s = tau
        else:
            s = -tau
        xp[i] = xi + s
        fp = theFunction(xp)[0]
        g[i] = (fp - f) / s
    return g


def findiff_H(theFunction, x):
    """Calculates the hessian of a function :math:`f` using finite differences

    :param theFunction: A function object that takes a vector as an
                        argument, and returns a tuple. The first
                        element of the tuple is the value of the
                        function :math:`f`, and the second is the
                        gradient of the function.  The other elements
                        are not used.

    :type theFunction: function

    :param x: argument of the function
    :type x: numpy.array

    :return: numpy matrix containing the hessian calculated by
             finite differences.
    :rtype: numpy.array

    """
    tau = 1.0e-7
    n = len(x)
    H = np.zeros((n, n))
    g = theFunction(x)[1]
    eye = np.eye(n, n)
    for i in range(n):
        xi = x.item(i)
        if abs(xi) >= 1:
            s = tau * xi
        elif xi >= 0:
            s = tau
        else:
            s = -tau
        ei = eye[i]
        gp = theFunction(x + s * ei)[1]
        H[:, i] = (gp - g).flatten() / s
    return H


def checkDerivatives(theFunction, x, names=None, logg=False):
    """Verifies the analytical derivatives of a function by comparing
    them with finite difference approximations.

    :param theFunction: A function object that takes a vector as an argument,
        and returns a tuple:

        - The first element of the tuple is the value of the
          function :math:`f`,
        - the second is the gradient of the function,
        - the third is the hessian.

    :type theFunction: function

    :param x: arguments of the function
    :type x: numpy.array

    :param names: the names of the entries of x (for reporting).
    :type names: list(string)
    :param logg: if True, messages will be displayed.
    :type logg: bool


    :return: tuple f, g, h, gdiff, hdiff where

          - f is the value of the function at x,
          - g is the analytical gradient,
          - h is the analytical hessian,
          - gdiff is the difference between the analytical gradient
            and the finite difference approximation
          - hdiff is the difference between the analytical hessian
            and the finite difference approximation

    :rtype: float, numpy.array,numpy.array,  numpy.array,numpy.array

    """
    x = np.array(x, dtype=float)
    f, g, h = theFunction(x)
    g_num = findiff_g(theFunction, x)
    gdiff = g - g_num
    if logg:
        if names is None:
            names = [f'x[{i}]' for i in range(len(x))]
        logger.detailed('x\t\tGradient\tFinDiff\t\tDifference')
        for k, v in enumerate(gdiff):
            logger.detailed(f'{names[k]:15}\t{g[k]:+E}\t{g_num[k]:+E}\t{v:+E}')

    h_num = findiff_H(theFunction, x)
    hdiff = h - h_num
    if logg:
        logger.detailed('Row\t\tCol\t\tHessian\tFinDiff\t\tDifference')
        for row in range(len(hdiff)):
            for col in range(len(hdiff)):
                logger.detailed(
                    f'{names[row]:15}\t{names[col]:15}\t{h[row,col]:+E}\t'
                    f'{h_num[row,col]:+E}\t{hdiff[row,col]:+E}'
                )
    return f, g, h, gdiff, hdiff


def getPrimeNumbers(n):
    """Get a given number of prime numbers

    :param n: number of primes that are requested
    :type n: int

    :return: array with prime numbers
    :rtype: list(int)

    :raise biogemeError: if the requested number is non positive or a float

    """
    total = 0
    upperBound = 100
    if n <= 0:
        raise excep.biogemeError(f'Incorrect number: {n}')

    while total < n:
        upperBound *= 10
        primes = calculatePrimeNumbers(upperBound)
        total = len(primes)
    try:
        return primes[0:n]
    except TypeError as e:
        raise excep.biogemeError(f'Incorrect number: {n}') from e


def calculatePrimeNumbers(upperBound):
    """Calculate prime numbers

    :param upperBound: prime numbers up to this value will be computed
    :type upperBound: int

    :return: array with prime numbers
    :rtype: list(int)

    :raise biogemeError: if the upperBound is incorrectly defined
        (negative number, e.g.)

    >>> tools.calculatePrimeNumbers(10)
    [2, 3, 5, 7]

    """
    try:
        mywork = list(range(0, upperBound + 1))
    except TypeError as e:
        raise excep.biogemeError(f'Incorrect value: {upperBound}') from e

    try:
        largest = int(np.ceil(np.sqrt(float(upperBound))))
    except ValueError as e:
        raise excep.biogemeError(f'Incorrect value: {upperBound}') from e

    # Remove all multiples
    for i in range(2, largest + 1):
        if mywork[i] != 0:
            for k in range(2 * i, upperBound + 1, i):
                mywork[k] = 0
    # Gather non zero entries, which are the prime numbers
    myprimes = []
    for i in range(1, upperBound + 1):
        if mywork[i] != 0 and mywork[i] != 1:
            myprimes += [mywork[i]]

    return myprimes


def countNumberOfGroups(df, column):
    """
    This function counts the number of groups of same value in a column.
    For instance: 1,2,2,3,3,3,4,1,1  would give 5.

    Example::

        >>>df = pd.DataFrame({'ID': [1, 1, 2, 3, 3, 1, 2, 3],
                              'value':[1000,
                                       2000,
                                       3000,
                                       4000,
                                       5000,
                                       5000,
                                       10000,
                                       20000]})
        >>>tools.countNumberOfGroups(df,'ID')
        6

        >>>tools.countNumberOfGroups(df,'value')
        7

    """
    df['_biogroups'] = (df[column] != df[column].shift(1)).cumsum()
    return len(df['_biogroups'].unique())


def likelihood_ratio_test(model1, model2, significance_level=0.95):
    """This function performs a likelihood ratio test between a
    restricted and an unrestricted model.

    :param model1: the final loglikelood of one model, and the number of
                   estimated parameters.
    :type model1: tuple(float, int)

    :param model2: the final loglikelood of the other model, and
                   the number of estimated parameters.
    :type model2: tuple(float, int)

    :param significance_level: level of significance of the test. Default: 0.95
    :type significance_level: float

    :return: a tuple containing:

                  - a message with the outcome of the test
                  - the statistic, that is minus two times the difference
                    between the loglikelihood  of the two models
                  - the threshold of the chi square distribution.

    :rtype: (str, float, float)

    :raise biogemeError: if the unrestricted model has a lower log
        likelihood than the restricted model.

    """

    loglike_m1, df_m1 = model1
    loglike_m2, df_m2 = model2
    if loglike_m1 > loglike_m2:
        if df_m1 < df_m2:
            raise excep.biogemeError(
                f'The unrestricted model {model2} has a '
                f'lower log likelihood than the restricted one {model1}'
            )
        loglike_ur = loglike_m1
        loglike_r = loglike_m2
        df_ur = df_m1
        df_r = df_m2
    else:
        if df_m1 >= df_m2:
            raise excep.biogemeError(
                f'The unrestricted model {model1} has a '
                f'lower log likelihood than the restricted one {model2}'
            )
        loglike_ur = loglike_m2
        loglike_r = loglike_m1
        df_ur = df_m2
        df_r = df_m1

    stat = -2 * (loglike_r - loglike_ur)
    chi_df = df_ur - df_r
    threshold = chi2.ppf(significance_level, chi_df)
    if stat <= threshold:
        final_msg = f'H0 cannot be rejected at level {significance_level}'
    else:
        final_msg = f'H0 can be rejected at level {significance_level}'
    return final_msg, stat, threshold

import unittest

import numpy

import chainer
from chainer import cuda
from chainer import functions
from chainer import gradient_check
from chainer import testing
from chainer.testing import attr
from chainer.testing import condition


@testing.parameterize(*testing.product({
    'shape': [(3, 2), ()],
    'dtype': [numpy.float16, numpy.float32, numpy.float64],
}))
class TestClippedReLU(unittest.TestCase):

    def setUp(self):
        self.x = numpy.random.uniform(-1, 1, self.shape).astype(self.dtype)
        # Avoid values around zero and z for stability of numerical gradient
        for i in numpy.ndindex(self.shape):
            if -0.01 < self.x[i] < 0.01 or 0.74 < self.x[i] < 0.76:
                self.x[i] = 0.5

        self.gy = numpy.random.uniform(-1, 1, self.shape).astype(self.dtype)
        self.z = 0.75
        self.check_backward_options = {}
        if self.dtype == numpy.float16:
            self.check_backward_options = {'eps': 2.0 ** -8}

    def check_forward(self, x_data):
        x = chainer.Variable(x_data)
        y = functions.clipped_relu(x, self.z)
        self.assertEqual(y.data.dtype, self.dtype)

        y_expect = self.x.copy()
        for i in numpy.ndindex(self.x.shape):
            if self.x[i] < 0:
                y_expect[i] = 0
            elif self.x[i] > self.z:
                y_expect[i] = self.z

        testing.assert_allclose(y_expect, y.data)

    @condition.retry(3)
    def test_forward_cpu(self):
        self.check_forward(self.x)

    @attr.gpu
    @condition.retry(3)
    def test_forward_gpu(self):
        self.check_forward(cuda.to_gpu(self.x))

    def check_backward(self, x_data, y_grad):
        gradient_check.check_backward(
            functions.ClippedReLU(self.z), x_data, y_grad,
            **self.check_backward_options)

    @condition.retry(3)
    def test_backward_cpu(self):
        self.check_backward(self.x, self.gy)

    @attr.gpu
    @condition.retry(3)
    def test_backward_gpu(self):
        self.check_backward(cuda.to_gpu(self.x), cuda.to_gpu(self.gy))


testing.run_module(__name__, __file__)

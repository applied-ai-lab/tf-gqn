"""
Quick test script to check ELBO optimization on GQN with random
toy data.
"""

import os
import sys
SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
TF_GQN_HOME = os.path.abspath(os.path.join(SCRIPT_PATH, '..'))
sys.path.append(TF_GQN_HOME)

import tensorflow as tf
import numpy as np

from gqn.gqn_params import GQN_DEFAULT_CONFIG
from gqn.gqn_graph import gqn_draw
from gqn.gqn_objective import gqn_draw_elbo

# constants
_BATCH_SIZE = 1
_CONTEXT_SIZE = GQN_DEFAULT_CONFIG.CONTEXT_SIZE
_DIM_POSE = GQN_DEFAULT_CONFIG.POSE_CHANNELS
_DIM_H_IMG = GQN_DEFAULT_CONFIG.IMG_HEIGHT
_DIM_W_IMG = GQN_DEFAULT_CONFIG.IMG_WIDTH
_DIM_C_IMG = GQN_DEFAULT_CONFIG.IMG_CHANNELS
_SEQ_LENGTH = GQN_DEFAULT_CONFIG.SEQ_LENGTH
_MAX_TRAIN_STEPS = 50

# input placeholders
query_pose = tf.placeholder(
    shape=[_BATCH_SIZE, _DIM_POSE], dtype=tf.float32)
target_frame = tf.placeholder(
    shape=[_BATCH_SIZE, _DIM_H_IMG, _DIM_W_IMG, _DIM_C_IMG],
    dtype=tf.float32)
context_poses = tf.placeholder(
    shape=[_BATCH_SIZE, _CONTEXT_SIZE, _DIM_POSE],
    dtype=tf.float32)
context_frames = tf.placeholder(
    shape=[_BATCH_SIZE, _CONTEXT_SIZE, _DIM_H_IMG, _DIM_W_IMG, _DIM_C_IMG],
    dtype=tf.float32)

# graph definition
net, ep_gqn = gqn_draw(
    query_pose=query_pose,
    target_frame=target_frame,
    context_poses=context_poses,
    context_frames=context_frames,
    model_params=GQN_DEFAULT_CONFIG,
    is_training=True
)

# loss definition
mu_target = net
sigma_target = tf.constant(  # additional parameter tuned during training
    value=1.0, dtype=tf.float32,
    shape=[_BATCH_SIZE, _DIM_H_IMG, _DIM_W_IMG, _DIM_C_IMG])
mu_q, sigma_q, mu_pi, sigma_pi = [], [], [], []
# collecting endpoints for ELBO computation
for i in range(_SEQ_LENGTH):
  mu_q.append(ep_gqn["mu_q_%d" % i])
  sigma_q.append(ep_gqn["sigma_q_%d" % i])
  mu_pi.append(ep_gqn["mu_pi_%d" % i])
  sigma_pi.append(ep_gqn["sigma_pi_%d" % i])
elbo, ep_elbo = gqn_draw_elbo(
    mu_target, sigma_target,
    mu_q, sigma_q,
    mu_pi, sigma_pi,
    target_frame)

# define optimizer
optimizer = tf.train.AdamOptimizer()
grad_vars = optimizer.compute_gradients(loss=elbo)
updates = optimizer.apply_gradients(grads_and_vars=grad_vars)

# print computational endpoints
print("GQN enpoints:")
for ep, t in ep_gqn.items():
  print(ep, t)

# overfit the graph to a random input data point
rnd_query_pose = np.random.rand(_BATCH_SIZE, _DIM_POSE)
rnd_target_frame = np.random.rand(_BATCH_SIZE, _DIM_H_IMG, _DIM_W_IMG, _DIM_C_IMG)
rnd_context_poses = np.random.rand(_BATCH_SIZE, _CONTEXT_SIZE, _DIM_POSE)
rnd_context_frames = np.random.rand(_BATCH_SIZE, _CONTEXT_SIZE, _DIM_H_IMG, _DIM_W_IMG, _DIM_C_IMG)

with tf.Session() as sess:
  sess.run(tf.global_variables_initializer())
  for step in range(_MAX_TRAIN_STEPS):
    _elbo, _grad_vars, _updates = sess.run(
        [elbo, grad_vars, updates],
        feed_dict={
            query_pose : rnd_query_pose,
            target_frame : rnd_target_frame,
            context_poses : rnd_context_poses,
            context_frames : rnd_context_frames,
        })
    if step == 0:  # print gradient setup after first feed
      print("Gradient shapes:")
      for _grad, _var in _grad_vars:
        print(_grad.shape, _var.shape)
    print("Training step: %d" % (step + 1, ))
    print(_elbo)

print("TEST PASSED!")

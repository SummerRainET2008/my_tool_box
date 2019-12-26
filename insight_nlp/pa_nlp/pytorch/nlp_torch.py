#author: Tian Xia (SummerRainET2008@gmail.com)

from pa_nlp import *
from pa_nlp.nlp import Logger
from pa_nlp import nlp
from pa_nlp.pytorch import *
import torch

class Dense(nn.Module):
  def __init__(self,
               linear_layer: nn.Linear,
               activation=nn.functional.leaky_relu):
    super(Dense, self).__init__()
    self._linear_layer = linear_layer
    self._activation = activation if activation is not None else lambda x: x

  def forward(self, x: torch.Tensor):
    return self._activation(self._linear_layer(x))

class RNNEncoder(nn.Module):
  def __init__(self,
               layer_num,
               emb_dim,
               hidden_dim,
               out_dropout: float):
    super(RNNEncoder, self).__init__()
    self._bi_rnn = nn.GRU(
      input_size=emb_dim, hidden_size=hidden_dim, num_layers=layer_num,
      batch_first=True, bidirectional=True
    )

    self._combine_dense = Dense(nn.Linear(2 * hidden_dim, hidden_dim))
    self._out_dropout = nn.Dropout(out_dropout)
    self._layer_num = layer_num

    self._hidden_dim = hidden_dim

  def _init_hidden(self, batch_size):
    weight = next(self.parameters())
    hidden = weight.new_zeros(2 * self._layer_num, batch_size, self._hidden_dim)

    return hidden

  def forward(self, x, mask, packed_input=False):
    '''
    x: [batch, max-seq, emb-dim]
    mask: [batch, max-seq]
    '''
    hidden = self._init_hidden(x.size(0))
    x_length = mask.sum(1)

    #note, when pack_padded_sequence is needed, the batch has to been sorted by
    #their real lengths.
    if packed_input:
      x = torch.nn.utils.rnn.pack_padded_sequence(
        x, x_length, batch_first=True
      )
    output, _ = self._bi_rnn(x, hidden)
    if packed_input:
      output, _ = torch.nn.utils.rnn.pad_packed_sequence(
        output, batch_first=True, total_length=mask.size(1)
      )

    output = self._combine_dense(output)
    output = self._out_dropout(output)

    return output

class Attention(nn.Module):
  def __init__(self,
               query_dim,
               values_dim,
               atten_dim):
    super(Attention, self).__init__()
    self._query_dense = Dense(nn.Linear(query_dim, atten_dim))
    self._values_dense = Dense(nn.Linear(values_dim, atten_dim))
    self._logit_out = Dense(nn.Linear(atten_dim, 1))

  def forward(self, query, values, mask):
    '''
    query: [batch, dim]
    values: [batch, len, dim]
    mask: [batch, max-seq], IntTensor
    '''
    m = self._values_dense(values)
    m += self._query_dense(query).unsqueeze(1).expand_as(m)
    logit = self._logit_out(torch.tanh(m)).squeeze(2)
    logit.data.masked_fill_(torch.logical_not(mask), -1e-9)
    prob = nn.functional.softmax(logit, dim=1)
    output = prob.unsqueeze(1).matmul(values).squeeze(1)

    return output

class VallinaDecoder(nn.Module):
  def __init__(self,
               emb_dim,
               hidden_dim,
               enc_outputs_dim,
               out_dropout):
    super(VallinaDecoder, self).__init__()

    self._rnn_cell1 = nn.GRUCell(emb_dim, hidden_dim)
    self._enc_attn = Attention(hidden_dim, enc_outputs_dim, enc_outputs_dim)
    self._rnn_cell2 = nn.GRUCell(enc_outputs_dim, hidden_dim)
    self._x_dense = Dense(nn.Linear(emb_dim, hidden_dim))

    self._out_dropout = nn.Dropout(out_dropout)

  def forward(self, x, hidden, enc_outputs, enc_mask):
    '''
    x: [batch, emb-dim]
    hidden: [batch, hidden-dim]
    x_mask: [batch, max-seq]
    enc_output: [batch, max-seq, dim]
    '''
    hidden = self._rnn_cell1(x, hidden)
    attn_enc = self._enc_attn(hidden, enc_outputs, enc_mask)
    hidden = self._rnn_cell2(attn_enc, hidden)
    output = torch.tanh(
      self._x_dense(x) + attn_enc + hidden
    )
    output = self._out_dropout(output)

    return output, hidden



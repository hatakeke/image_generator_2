#encoding:utf-8

from .importer import *
from .base_module import *

class Discriminator(nn.Module):
	def __init__(self):
		super().__init__()
		self.minbatch_std = MiniBatchStd()
		#畳み込みモジュールの設定を1つずつしていく
		scale = 1
		#inchs:畳み込み層への入力データの解像度
		inchs  = np.array([256,128, 64,32,16, 8], dtype=np.uint32)*scale
		#outchs:畳み込み層からの出力データの解像度
		outchs = np.array([512,256,128,64,32,16], dtype=np.uint32)*scale
		#sizes:畳み込み層の入力チャネル数
		sizes  = np.array([  1,  4,  8,16,32,64], dtype=np.uint32)
		#最後の層のみ、それを示すフラグをTrueにしておく
		finals = np.array([True, False, False, False, False, False], dtype=np.bool)
		#blockには畳み込み層を格納、fromRGBsは入力画像(RGB3チャネル)を受け取るための層を格納
		blocks, fromRGBs = [], []
		for s, inch, outch, final in zip(sizes, inchs, outchs, finals):
			fromRGBs.append(nn.Conv2d(3, inch, 1, padding=0))
			blocks.append(ConvModuleD(s, inch, outch, final=final))
		self.fromRGBs = nn.ModuleList(fromRGBs)
		self.blocks = nn.ModuleList(blocks)
	#resは進捗パラメーター
	def forward(self, x, res):
		#何層目まで畳み込みを計算するかをresとする
		res = min(res, len(self.blocks))#resが畳み込み層の数より大きくならないようにする
		eps = 1e-7
		nlayer = max(int(res-eps),0)#resがeps以下なら0とみなす
		#最初の層に通しておく
		x_first = self.fromRGBs[nlayer](x)
		x_first = self.blocks[nlayer](x_first)
		if nlayer==0:
			x = x_first
		else:
			# low resolution
			x_sml = F.adaptive_avg_pool2d(x, x_first.shape[2:4])
			x_sml = self.fromRGBs[nlayer-1](x_sml)
			alpha = res - int(res-eps)
			x = (1-alpha)*x_sml + alpha*x_first
		for i in range(nlayer):
			x = self.blocks[nlayer-1-i](x)
		return x


'''
Created on 2015-7-14

@author: johnw
'''
from num2word_EN import n2w, to_card, to_ord, to_ordnum
print to_card(39275.00)
print n2w.to_currency((39275.00, 0))
print n2w.to_currency((39275.00, 0), longval=False)


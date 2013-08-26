import sys
import math
from functools import partial
from operator import add
import os
import re

if len(sys.argv) < 2:
  print('Usage: vzon.py <bill_name.txt>')
  exit(1)

name_ext=[]
try:
  name_ext = str(sys.argv[1]).split('.')
except:
  print('Invalid bill file name')
  exit(1)

if len(name_ext) < 2:
  print('Bill file name must have a valid extension')
  exit(1)

os.system('pdftotext ' + sys.argv[1]) 
txt_bill_name = name_ext[0] + '.txt'   
tmp_name = '_' + txt_bill_name
os.system("sed '/^Total\|^Detail\|^\$/!d ' {0} > {1}".format(txt_bill_name, tmp_name))

amounts={} #Total, Shared, or by Phone Number
details={} #Name associated with account
phone_num_regex = '([0-9]{3}-[0-9]{3}-[0-9]{4})'
amnt_regex = '\$([0-9]+\.[0-9]+)'
match_strings=['Total Current Charges$',
               'Total Current Charges for ' + phone_num_regex,
               'Detail for ([^:]*): ' + phone_num_regex,
               'Total Account Charges and Credits']

def eq(a, b, eps=0.0001 ):
      return abs(math.log( a ) - math.log(b)) <=  eps

def get_dollars(line):
    return re.search(amnt_regex,line).group(1)

def add_total_name(amounts, name):
  amounts[name] = 0
  def on_next_iter(line):
    value = 0
    try:
      value = get_dollars(line)
    except:
      print("Parsing the following amount for " 
          + name + " was not possible, input was: " + str(line))
      exit(1)
    amounts[name] = float(value)
  return on_next_iter

def add_shared(amounts):
  return add_total_name(amounts,'Shared')

def add_total(amounts):
  return add_total_name(amounts,'Total')

def add_detail(details, name, phone_num):
  details[phone_num] = name
  return None

re_str_and_funcs = zip( match_strings,
                        [partial(add_total,amounts), 
                        partial(add_total_name,amounts),
                        partial(add_detail,details),
                        partial(add_shared,amounts),
                        ]
                      )

#parse file and populate dictionaries
with open(tmp_name,'r') as b:
  on_next_iter = None
  for line in b:
    if on_next_iter:
      on_next_iter(line)
      on_next_iter = None
      continue
    for (regx, f_extract) in re_str_and_funcs:
      match = re.search(regx,line)
      if match:
        try:
          on_next_iter = f_extract(*match.groups())
        except:
          print("Wrong number of arguments provided to: " + f_extract.func.__name__)
          exit(1)
        break

ind_bills = [x for x in amounts.items() if x[0] != 'Shared' and x[0] != 'Total']
shared_bill = amounts['Shared']/len(ind_bills)
pars_total = amounts['Total']
full_ind_bills = [(phone,amount+shared_bill) for (phone,amount) in ind_bills]
total_from_ind = reduce(add, [amount for (_,amount) in full_ind_bills], 0)
if eq(total_from_ind,pars_total):
  for (key,amount) in full_ind_bills:
    if key in details:
      print(details[key] + '-' + key + ': $' +  str(amount))
    else:
      print(key + ': $' + str(amount))
else:
  print('Error: mismatch between computed total and parsed total. Parsed: $' + pars_total +
         ' Computed: $' + total_from_ind)
  exit(1)
print('Total: $' + str(total_from_ind))

os.remove(txt_bill_name)
os.remove(tmp_name)

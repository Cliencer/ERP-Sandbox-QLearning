import numpy as np
import random
import json
import pickle
import os

ErpInfo={
    'management_fee':10, # 每季度管理费
    'factory':{
        'small': {'capacity': 2, 'price': 180, 'rent': 18, 'score': 7},
        'medium': {'capacity': 3, 'price': 300, 'rent': 30, 'score': 8},
        'large': {'capacity': 4, 'price': 400, 'rent': 40, 'score': 10}
    },

    'production_line' : {
        'manual': {'install_time': 0, 'install_cost': 35, 'production_time': 2, 'transformation_time': 0, 'transformation_cost': 0, 'maintenance': 5, 'residual_value': 5, 'value':35,'depreciation': 10, 'score': 0},
        'automatic': {'install_time': 3, 'install_cost': 50, 'production_time': 1, 'transformation_time': 1, 'transformation_cost': 20, 'maintenance': 20, 'residual_value': 30,'value':150, 'depreciation': 30, 'score': 8},
        'flexible': {'install_time': 4, 'install_cost': 50, 'production_time': 1, 'transformation_time': 0, 'transformation_cost': 0, 'maintenance': 20, 'residual_value': 40, 'value':200, 'depreciation': 40, 'score': 10},
        'lease': {'install_time': 0, 'install_cost': 0, 'production_time': 1, 'transformation_time': 1, 'transformation_cost': 20, 'maintenance': 65, 'residual_value': -65, 'value':0, 'depreciation': 0, 'score': 0}
    },

    'product' : {
        'P1': {'development_time': 2, 'development_cost': 10, 'materials': ['R1'], 'processing_cost': 10, 'score': 7},
        'P2': {'development_time': 3, 'development_cost': 10, 'materials': ['R2', 'R3'], 'processing_cost': 10, 'score': 8},
        'P3': {'development_time': 4, 'development_cost': 10, 'materials': ['R1', 'R3', 'R4'], 'processing_cost': 10, 'score': 9},
        'P4': {'development_time': 6, 'development_cost': 10, 'materials': ['R1', 'R2', 'R3', 'R4'], 'processing_cost': 10, 'score': 10}
    },

    'material' : {
        'R1': {'transport_time': 1, 'price': 10, 'emergency_price': 20},
        'R2': {'transport_time': 1, 'price': 10, 'emergency_price': 20},
        'R3': {'transport_time': 2, 'price': 10, 'emergency_price': 20},
        'R4': {'transport_time': 2, 'price': 10, 'emergency_price': 20}
    },

    'market' : {
        'local': {'development_time': 1, 'development_cost': 10, 'score': 7},
        'regional': {'development_time': 1, 'development_cost': 10, 'score': 7},
        'national': {'development_time': 2, 'development_cost': 10, 'score': 8},
        'continental': {'development_time': 3, 'development_cost': 10, 'score': 9},
        'international': {'development_time': 4, 'development_cost': 10, 'score': 10}
    },

    'iso' : {
        'ISO9000': {'development_time': 2, 'development_cost': 10, 'score': 8},
        'ISO14000': {'development_time': 2, 'development_cost': 20, 'score': 10}
    },

    'loan':{
        'long': {'profit':0.1,'maxYear':5},
        'short':{'profit':0.05,'maxYear':1}
    },
    'order':{

    }
}

exerciseInfo = {
    'wrongAction':1,  #逻辑操作错误扣分
    'BanAction':0.1, #游戏禁止行为扣分
}


# def dict_mapped_tup(list):
    
#     map_tuple = []
#     for dictionary in list:
#         for key, value in dictionary.items():
#             if isinstance(value, dict):
#                 map_tuple.extend((key, subkey, subvalue) for subkey, subvalue in dict_mapped_tup(value))
#             else:
#                 map_tuple.append((key, value))
#     return map_tuple


class ERPSandbox:
    def __init__(self):
        # 初始状态
        self.cash = 600  # 初始现金
        self.material_inventory = {'R1':0,'R2':0,'R3':0,'R4':0}  # 初始库存
        self.material_onRoad = {'quarter1':{'R1':0,'R2':0,'R3':0,'R4':0},
                                'quarter2':{'R1':0,'R2':0,'R3':0,'R4':0}}
        self.factory = []  # 初始厂房 {'type':'small','isRent':False,'rentQuarter':1,'Lines':[{'type':'manual','isBuilding':False,'isChanging':False,'Product':'P1'}]}
        self.research_progress = {'P1':{'remainTime':ErpInfo['product']['P1']['development_time'],'isDeveloped':False,'isDeveloping':False},
                                  'P2':{'remainTime':ErpInfo['product']['P2']['development_time'],'isDeveloped':False,'isDeveloping':False},
                                  'P3':{'remainTime':ErpInfo['product']['P3']['development_time'],'isDeveloped':False,'isDeveloping':False},
                                  'P4':{'remainTime':ErpInfo['product']['P4']['development_time'],'isDeveloped':False,'isDeveloping':False}}  # 研发进度
        self.market_qualification = {'local':{'remainTime':ErpInfo['market']['local']['development_time'],'isDeveloped':False},
                                     'regional':{'remainTime':ErpInfo['market']['regional']['development_time'],'isDeveloped':False},
                                     'national':{'remainTime':ErpInfo['market']['national']['development_time'],'isDeveloped':False},
                                     'continental':{'remainTime':ErpInfo['market']['continental']['development_time'],'isDeveloped':False},
                                     'international':{'remainTime':ErpInfo['market']['international']['development_time'],'isDeveloped':False}}  # 市场资质 每次研发减1
        self.iso_qualification = {'ISO9000':{'remainTime':ErpInfo['iso']['ISO9000']['development_time'],'isDeveloped':False},
                                  'ISO14000':{'remainTime':ErpInfo['iso']['ISO14000']['development_time'],'isDeveloped':False}}  # ISO资质
        self.orders = []  # 当前订单 {'product':'P1','num':4,'completeQuarter':3,'cash':150,'cashQuarter':3}
        self.accounts_receivable = []  # 应收账款 {'cash':150,'cashQuarter':3}
        self.accounts_payable = []  # 应付账款 {'cash':150,'cashQuarter':3}
        self.accounts_long_loan = [] # 长期借款 {'cash':150,'Year':2,'quarter':1}
        self.accounts_short_loan = [] # 短期借款 {'cash':150,'Year':2,'quarter':1}
        self.quarter = 1  # 当前季度 0年初 5年末
        self.year = 1  # 当前年份
        self.score = 0  # 当前得分
        self.ownerInterest = 600 #所有者权益
        self.maxLoan = 3*self.ownerInterest
        self.lossPool = 0 #亏损池
        self.accounts_book = []

        self.refresh_book('JCXJ',self.cash,1)
        for i in range(0,30):
            self.refresh_book('GLF',-ErpInfo['management_fee'],i)  

    def refresh_book(self,subject,cash,quarter=None):
        if quarter == None:
            quarter = self.year*4+self.quarter-4
        while quarter > len(self.accounts_book):
            self.accounts_book.append({'JCXJ':0,
                               'ZFSNSF':0,'GGF':0,
                               'CHCDBJ':0,'CFCDLX':0,
                               'CHDDBJ':0,'CFDDLX':0,
                               'ZFYCL':0,'DDWYSS':0,
                               'YSZKRZQXJ':0,
                               'YSZKRZ':0,
                               'DKQXJ':0,
                               'SQCD':0,'SQDD':0,
                               'XJDDRZ':0,'TXDSJE':0,
                               'JYQXJ':0,
                               'CFZLF':0,'CFGMZC':0,'GJSCX':0,
                               'JGF':0,'ZCF':0,'BMSCX':0,
                               'GLF':0,
                               'CPKFF':0,'ISOKFF':0,'SCKFF':0,'SBWXF':0,
                               'JMXJ':0})
            
        self.accounts_book[quarter-1][subject] += cash
        for i in range(quarter-1,len(self.accounts_book)):
            if i>0: 
                self.accounts_book[i]['JCXJ'] = self.accounts_book[i-1]['SBWXF']
            self.accounts_book[i]['YSZKRZQXJ']=self.accounts_book[i]['JCXJ']+\
                                                self.accounts_book[i]['ZFSNSF']+\
                                                self.accounts_book[i]['GGF']+\
                                                self.accounts_book[i]['CHCDBJ']+\
                                                self.accounts_book[i]['CFCDLX']+\
                                                self.accounts_book[i]['CHDDBJ']+\
                                                self.accounts_book[i]['CFDDLX']+\
                                                self.accounts_book[i]['ZFYCL']+\
                                                self.accounts_book[i]['DDWYSS']
            self.accounts_book[i]['DKQXJ']=self.accounts_book[i]['YSZKRZQXJ']+\
                                            self.accounts_book[i]['YSZKRZ']
            # 贷款前现金判定是否破产
            self.accounts_book[i]['JYQXJ']=self.accounts_book[i]['DKQXJ']+\
                                            self.accounts_book[i]['SQCD']+\
                                            self.accounts_book[i]['SQDD']+\
                                            self.accounts_book[i]['XJDDRZ']+\
                                            self.accounts_book[i]['TXDSJE']
    
            self.accounts_book[i]['JMXJ']=self.accounts_book[i]['JYQXJ']+\
                                            self.accounts_book[i]['CFZLF']+\
                                            self.accounts_book[i]['CFGMZC']+\
                                            self.accounts_book[i]['GJSCX']+\
                                            self.accounts_book[i]['JGF']+\
                                            self.accounts_book[i]['ZCF']+\
                                            self.accounts_book[i]['BMSCX']+\
                                            self.accounts_book[i]['GLF']+\
                                            self.accounts_book[i]['CPKFF']+\
                                            self.accounts_book[i]['ISOKFF']+\
                                            self.accounts_book[i]['SCKFF']+\
                                            self.accounts_book[i]['SBWXF']
            
    def print(self,str):
        print(f'第{self.year}年第{self.quarter},AI{str},{self.cash},{self.reward}')

    def reset(self):
        # 初始状态
        self.cash = 600  # 初始现金
        self.material_inventory = {'R1':0,'R2':0,'R3':0,'R4':0}  # 初始库存
        self.material_onRoad = {'quarter1':{'R1':0,'R2':0,'R3':0,'R4':0},
                                'quarter2':{'R1':0,'R2':0,'R3':0,'R4':0}}
        self.factory = []  # 初始厂房 {'type':'small','isRent':False,'rentQuarter':1,'Lines':[{'type':'manual','isBuilding':False,'isChanging':False,'Product':'P1'}]}
        self.research_progress = {'P1':{'remainTime':ErpInfo['product']['P1']['development_time'],'isDeveloped':False,'isDeveloping':False},
                                  'P2':{'remainTime':ErpInfo['product']['P2']['development_time'],'isDeveloped':False,'isDeveloping':False},
                                  'P3':{'remainTime':ErpInfo['product']['P3']['development_time'],'isDeveloped':False,'isDeveloping':False},
                                  'P4':{'remainTime':ErpInfo['product']['P4']['development_time'],'isDeveloped':False,'isDeveloping':False}}  # 研发进度
        self.market_qualification = {'local':{'remainTime':ErpInfo['market']['local']['development_time'],'isDeveloped':False},
                                     'regional':{'remainTime':ErpInfo['market']['regional']['development_time'],'isDeveloped':False},
                                     'national':{'remainTime':ErpInfo['market']['national']['development_time'],'isDeveloped':False},
                                     'continental':{'remainTime':ErpInfo['market']['continental']['development_time'],'isDeveloped':False},
                                     'international':{'remainTime':ErpInfo['market']['international']['development_time'],'isDeveloped':False}}  # 市场资质 每次研发减1
        self.iso_qualification = {'ISO9000':{'remainTime':ErpInfo['iso']['ISO9000']['development_time'],'isDeveloped':False},
                                  'ISO14000':{'remainTime':ErpInfo['iso']['ISO14000']['development_time'],'isDeveloped':False}}  # ISO资质
        self.orders = []  # 当前订单 {'product':'P1','num':4,'completeQuarter':3,'cash':150,'cashQuarter':3}
        self.accounts_receivable = []  # 应收账款 {'cash':150,'cashQuarter':3}
        self.accounts_payable = []  # 应付账款 {'cash':150,'cashQuarter':3}
        self.accounts_long_loan = [] # 长期借款 {'cash':150,'Year':2,'quarter':1}
        self.accounts_short_loan = [] # 短期借款 {'cash':150,'Year':2,'quarter':1}
        self.quarter = 1  # 当前季度 0年初 5年末
        self.year = 1  # 当前年份
        self.score = 0  # 当前得分
        self.ownerInterest = 600 #所有者权益
        self.maxLoan = 3*self.ownerInterest
        self.lossPool = 0 #亏损池
        self.accounts_book = []

        self.refresh_book('JCXJ',self.cash,1)
        for i in range(0,30):
            self.refresh_book('GLF',-ErpInfo['management_fee'],i)  
        return self.get_state()

    def get_state(self):
        # 返回当前状态
        return {
            'cash': self.cash,
            'material_inventory': self.material_inventory,
            'material_onRoad':self.material_onRoad,
            'factory': self.factory,
            'research_progress': self.research_progress,
            'market_qualification': self.market_qualification,
            'iso_qualification': self.iso_qualification,
            'orders': self.orders,
            #'accounts_receivable': self.accounts_receivable,
            #'accounts_payable': self.accounts_payable,
            #'accounts_long_loan': self.accounts_long_loan,
            #'accounts_short_loan':self.accounts_short_loan,
            'quarter': self.quarter,
            'year': self.year,
            'score': self.score,
            ##'ownerInterest':self.ownerInterest,
            'accounts_book':json.dumps(self.accounts_book)
        }
    
    def tryUseCash(self,cash):
        if self.cash >= cash:
            self.cash -= cash
            return True
        else:
            self.reward-=exerciseInfo['wrongAction']
            return False

    def step(self, action):
        # 执行动作，更新状态，返回奖励和是否结束
        self.reward = 0
        done = False

        for uselessLoop in range(0,1):
        # 执行动作逻辑
            #建立厂房
            if action['type'] == 'build_factory':
                
                if self.quarter>4: 
                    self.reward-=exerciseInfo['BanAction']
                    break
                if len(self.factory)==4: #厂房满了直接惩罚
                    self.reward-=exerciseInfo['wrongAction']
                    break
                
                factory_type = action['factory_type']
                factory_buildType = action['factory_buildType']
                if factory_buildType == "buy":
                    if self.tryUseCash(ErpInfo['factory'][factory_type]['price']):
                        self.refresh_book('CFGMZC',-ErpInfo['factory'][factory_type]['price'])
                        self.score += ErpInfo['factory'][factory_type]['score'] #买厂房加分
                        self.factory.append ({'type':factory_type,
                                            'isRent':False,
                                            'rentQuarter':0,
                                            'maxCapacity':ErpInfo['factory'][factory_type],
                                            'linesNum':0,
                                            'lines':[]})
                        self.print(f'购买了{factory_type}厂房')
                elif factory_buildType == "rent":
                    if self.tryUseCash(ErpInfo['factory'][factory_type]['rent']):
                        self.refresh_book('CFZLF',-ErpInfo['factory'][factory_type]['rent'])
                        self.factory.append ({'type':factory_type,
                                            'isRent':True,
                                            'rentQuarter':self.quarter, #记录租赁厂房的季
                                            'maxCapacity':ErpInfo['factory'][factory_type],
                                            'linesNum':0,
                                            'lines':[]})
                        self.print(f'租赁了{factory_type}厂房')
            #买断厂房      
            elif action['type'] == 'buy_factory':
                
                if self.quarter>4: 
                    self.reward-=exerciseInfo['BanAction']
                    break
                factory_number = action['factory_number']
                if len(self.factory)==0 or factory_number>len(self.factory)-1: #没有厂房可以买断直接惩罚
                    self.reward-=exerciseInfo['wrongAction']
                    break
                factory = self.factory[factory_number]
                if not factory['isRent']: #选的厂房不需要买断也直接惩罚
                    self.reward-=exerciseInfo['wrongAction']
                    break
                needCash = ErpInfo['factory'][factory['type']]['price']
                if self.tryUseCash(needCash):
                    self.refresh_book('CFGMZC',-needCash)
                    self.score += ErpInfo['factory'][factory['type']]['score'] #买厂房加分
                    self.factory[factory_number]['isRent'] = False
                    self.factory[factory_number]['rentQuarter'] = 0
                    self.print(f'买断了厂房')
            #出售/退租厂房
            elif action['type'] == 'sell_factory':
                if self.quarter>4: 
                    self.reward-=exerciseInfo['BanAction']
                    break
                factory_number = action['factory_number']
                if len(self.factory) == 0 or factory_number>len(self.factory)-1: #没有厂房可以出售直接惩罚
                    self.reward-=exerciseInfo['wrongAction']
                    break
                factory = self.factory[factory_number]
                if factory['linesNum']>0: #选的厂房生产线没有关闭也直接惩罚
                    self.reward-=exerciseInfo['wrongAction']
                    break
                if factory['isRent']:
                    del self.factory[factory_number]
                    self.print(f'退租了厂房')
                else:
                    cash = ErpInfo['factory'][factory['type']]['price']
                    self.refresh_book('YSZKRZ',cash,self.year*4+self.quarter) #4个季度后的应收账款
                    self.accounts_receivable.append({'cash':cash,'cashQuarter':self.quarter})
                    self.score -= ErpInfo['factory'][factory['type']]['score'] #卖厂房扣分
                    del self.factory[factory_number]
                    self.print(f'出售了厂房')
                
            
            # 建造新生产线
            elif action['type'] == 'build_new_production_line':
                if self.quarter>4: 
                    self.reward-=exerciseInfo['BanAction']
                    break
                factory_number = action['factory_number']
                if len(self.factory) == 0 or factory_number>len(self.factory)-1: #选错厂房建造也直接惩罚
                    self.reward-=exerciseInfo['wrongAction']
                    break
                line_type = action['line_type']
                product_choose = action['product_choose']
                factory = self.factory[factory_number]
                if factory['linesNum'] == factory['maxCapacity']:  #产线满了直接惩罚
                    self.reward-=exerciseInfo['wrongAction']
                    break
                if self.tryUseCash(ErpInfo['production_line'][line_type]['install_cost']):
                    self.refresh_book('GJSCX',-ErpInfo['production_line'][line_type]['install_cost'])
                    isBuilding=True
                    buildingQuarter = ErpInfo['production_line'][line_type]['install_time']
                    if buildingQuarter==0:
                        isBuilding=False
                    self.factory[factory_number]['lines'].append({'type':line_type,
                                                                'isBuilding':isBuilding,
                                                                'buildingQuarter':buildingQuarter,
                                                                'isFinished':not isBuilding,
                                                                'isProducting':False,
                                                                'productingQuarter':0,
                                                                'isChanging':False,
                                                                'changingQuarter':0,
                                                                'RemainValue':ErpInfo['production_line'][line_type]['value'],
                                                                'isStartDepreciation':False,
                                                                'product':product_choose,
                                                                'productChangeTo':None})
                    factory['linesNum']+=1
                    self.print(f'新建造了{line_type}生产线')
            # 出售/退租生产线
            elif action['type'] == 'sell_production_line':
                if self.quarter>4: 
                    self.reward-=exerciseInfo['BanAction']
                    break
                factory_number = action['factory_number']
                if len(self.factory) == 0 or factory_number>len(self.factory)-1: #选错厂房也直接惩罚
                    self.reward-=exerciseInfo['wrongAction']
                    break
                line_number = action['line_number']
                factory = self.factory[factory_number]
                if len(factory['lines']) == 0 or line_number>len(factory['lines'])-1: #选错产线也直接惩罚
                    self.reward-=exerciseInfo['wrongAction']
                    break
                line = factory['lines'][line_number]
                lineType = line['type']
                if line['isProducting']: #正在生产的时候不能卖
                    self.reward-=exerciseInfo['BanAction']
                    break
                del factory['lines'][line_number]
                self.cash+=ErpInfo['production_line'][lineType]['residual_value']
                self.refresh_book('BMSCX',ErpInfo['production_line'][lineType]['residual_value'])
                if self.cash<0:
                    self.reward -= 9999
                    done = True
                self.print(f'出售了{lineType}生产线')
                
            # 继续建造生产线
            elif action['type'] == 'continue_build_production_line':
                if self.quarter>4: 
                    self.reward-=exerciseInfo['BanAction']
                    break
                factory_number = action['factory_number']
                if len(self.factory) == 0 or factory_number>len(self.factory)-1: #选错厂房也直接惩罚
                    self.reward-=exerciseInfo['wrongAction']
                    break
                line_number = action['line_number']
                factory = self.factory[factory_number]
                if len(factory['lines']) == 0 or line_number>len(factory['lines'])-1: #选错产线也直接惩罚
                    self.reward-=exerciseInfo['wrongAction']
                    break
                line = factory['lines'][line_number]
                if line['isBuilding'] or line['isFinished']: #不能选已经建成的和正在建设的
                    self.reward-=exerciseInfo['wrongAction']
                    break
                lineType = line['type']
                if self.tryUseCash(ErpInfo['production_line'][lineType]['install_cost']):
                    line['isBuilding'] = True
                    self.refresh_book('GMSCX',-ErpInfo['production_line'][lineType]['install_cost'])
                self.print(f'继续建造了{lineType}生产线')
            # 转产生产线
            elif action['type'] == 'change_production_line':
                if self.quarter>4: 
                    self.reward-=exerciseInfo['BanAction']
                    break
                factory_number = action['factory_number']
                if len(self.factory) == 0 or factory_number>len(self.factory)-1: #选错厂房也直接惩罚
                    self.reward-=exerciseInfo['wrongAction']
                    break
                line_number = action['line_number']
                factory = self.factory[factory_number]
                if len(factory['lines']) == 0 or line_number>len(factory['lines'])-1: #选错产线也直接惩罚
                    self.reward-=exerciseInfo['wrongAction']
                    break
                line = factory['lines'][line_number]
                toProduct = action['toProduct']
                if (not line['isFinished']) or line['isProducting'] or line['isChanging'] or line['product']==toProduct: #不能选正在生产的、未建设完的、已经在转产的, 转产的和现在一样的
                    self.reward-=exerciseInfo['wrongAction']
                    break
                lineType = line['type']
                if self.tryUseCash(ErpInfo['production_line'][lineType]['transformation_cost']):
                    if ErpInfo['production_line'][lineType]['transformation_time']==0:
                        line['product'] = toProduct
                    else:
                        line['productChangeTo'] = toProduct
                        line['isChanginging'] = True
                        line['changingQuarter'] = ErpInfo['production_line'][lineType]['transformation_time']
                    self.refresh_book('ZCF',-ErpInfo['production_line'][lineType]['transformation_cost'])
                    self.print(f'转产{lineType}生产线到{toProduct}')
            #生产产品
            elif action['type'] == 'produce':
                if self.quarter>4: 
                    self.reward-=exerciseInfo['BanAction']
                    break
                factory_number = action['factory_number']
                if len(self.factory) == 0 or factory_number>len(self.factory)-1: #选错厂房也直接惩罚
                    self.reward-=exerciseInfo['wrongAction']
                    break
                line_number = action['line_number']
                factory = self.factory[factory_number]
                if len(factory['lines']) == 0 or line_number>len(factory['lines'])-1: #选错产线也直接惩罚
                    self.reward-=exerciseInfo['wrongAction']
                    break
                line = factory['lines'][line_number]
                if (not line['isFinished']) or line['isProducting'] or line['isChanging']: #不能选正在生产的、未建设完的、在转产的
                    self.reward-=exerciseInfo['wrongAction']
                    break
                
                lineType = line['type']
                productType = line['product']
                isSuccess = True
                if not self.research_progress[productType]['isDeveloped']:
                    self.reward-=exerciseInfo['wrongAction'] #还没研究好的，不能生产
                    break
                for material in ErpInfo['product'][productType]['materials']:
                    if self.material_inventory[material]<1:
                        isSuccess = False
                if isSuccess:
                    for material in ErpInfo['product'][productType]['materials']:
                        self.material_inventory[material]-=1
                    if self.tryUseCash(10):
                        self.refresh_book('JGF',-10)
                        line['isProducting']=True
                        line['productingQuarter']=ErpInfo['production_line'][lineType]['production_time']
                    self.print(f'{lineType}生产线生产了{productType}')
                else:
                    self.reward-=exerciseInfo['wrongAction'] #生产材料不够的，直接惩罚
                    break
            
            #原材料采购
            elif action['type'] == 'buy_material_normal':
                if self.quarter>4: 
                    self.reward-=exerciseInfo['BanAction']
                    break
                
                material = action['material']
                if self.material_onRoad['quarter1'][material]+self.material_onRoad['quarter2'][material]>40:
                    self.reward-=exerciseInfo['wrongAction']
                    break
                num = action['num']
                time = ErpInfo['material'][material]['transport_time']
                self.refresh_book('ZFYCL',-ErpInfo['material'][material]['price']*num,self.year*4+self.quarter-4+time)
                self.accounts_payable.append({'cash':ErpInfo['material'][material]['price']*num,'cashQuarter':3})
                if time == 1:
                    self.material_onRoad['quarter1'][material]+=num
                else:
                    self.material_onRoad['quarter2'][material]+=num
                self.print(f'采购了{material}')

            #原材料紧急采购
            elif action['type'] == 'buy_material_emergency':
                if self.quarter>4: 
                    self.reward-=exerciseInfo['BanAction']
                    break
                material = action['material']
                num = action['num']
                if self.tryUseCash(ErpInfo['material'][material]['emergency_price']*num):
                    self.refresh_book('ZFYCL',-ErpInfo['material'][material]['emergency_price']*num)
                    self.material_inventory[material]+=num
                    self.print(f'紧急采购了{material}')


            # 研发产品
            elif action['type'] == 'research_product':
                if self.quarter>4: 
                    self.reward-=exerciseInfo['BanAction']
                    break
                product = action['product']
                if self.research_progress[product]['isDeveloped'] or self.research_progress[product]['isDeveloping']:
                    self.reward-=exerciseInfo['wrongAction']
                    break
                if self.tryUseCash(ErpInfo['product'][product]['development_cost']):
                    self.refresh_book('CPKFF',-ErpInfo['product'][product]['development_cost'])
                    self.research_progress[product]['isDeveloping'] = True
                    self.print(f'研发{product}')
                    
                


                    


            elif action['type'] == 'next_round': #下一回合
                #没有招标不让进入下一年
                # if self.quarter == 4 and ((not self.isAdvertised) or (not self.isOrdered)):
                #     self.reward-=exerciseInfo['wrongAction']
                #     break
                self.reward+=self.cash/10
                self.print(f'进入下一季')
                self.quarter += 1
                #检查厂房是否要交下一年租金
                for factory in self.factory:
                    if factory['isRent'] and factory['rentQuarter']==self.quarter:
                        self.refresh_book('CFZLF',-ErpInfo['factory'][factory_type]['rent'])
                for factory in self.factory:
                    for line in factory['lines']:
                        if self.quarter != 5:
                            #更新建造状态
                            if line['isBuilding']:
                                line['buildingQuarter']-=1
                                line['isBuilding']=False
                                if line['buildingQuarter']==0:
                                    line['isFinished']=True
                            #更新生产状态
                            if line['isProducting']:
                                line['productingQuarter']-=1
                                if line['productingQuarter']==0:
                                    line['isProducting']=False
                                    self.material_inventory[line['product']]+=1
                            #更新转产状态
                            if line['isChanging']:
                                line['changingQuarter']-=1
                                if line['changingQuarter']==0:
                                    line['isChanging']=False
                                    line['product']=line['productChangeTo']
                                    line['productChangeTo']=None
                        if self.quarter>5:
                            lineType = line['type']
                            #折旧计算
                            if line['isStartDepreciation']:
                                if line['RemainValue']>ErpInfo['production_line'][lineType]['residual_value']:
                                    line['RemainValue']-=ErpInfo['production_line'][lineType]['depreciation']
                            else:
                                line['isStartDepreciation']=True #第二年才开始计算折旧
                            #设备维修费
                            self.refresh_book('SBWXF',-ErpInfo['production_line'][lineType]['maintenance'])           
                
                #材料送货更新
                if self.quarter != 5:
                    for material in ErpInfo['material']:
                        self.material_inventory[material]+=self.material_onRoad['quarter1'][material]
                        self.material_onRoad['quarter1'][material] = self.material_onRoad['quarter2'][material]
                        self.material_onRoad['quarter2'][material] = 0
                #研究更新
                    for product in ErpInfo['product']:
                        if  (not self.research_progress[product]['isDeveloped']) and self.research_progress[product]['isDeveloping']:
                            self.research_progress[product]['remainTime']-=1
                            self.research_progress[product]['isDeveloping'] = False
                            if self.research_progress[product]['remainTime'] == 0:
                                 self.research_progress[product]['isDeveloped'] = True
                    for account_num in range(len(self.accounts_payable)):
                        self.accounts_payable[account_num]['cashQuarter']-=1
                        if self.accounts_payable[account_num]['cashQuarter'] == 0:
                            del self.accounts_payable[account_num]
                    for account_num in range(len(self.accounts_receivable)):
                        self.accounts_receivable[account_num]['cashQuarter']-=1
                        if self.accounts_receivable[account_num]['cashQuarter'] == 0:
                            del self.accounts_receivable[account_num]
                              

                
                if self.quarter > 5:
                    self.quarter = 1
                    self.year += 1
                
                

                self.cash = self.accounts_book[self.quarter+self.year*4-4]["DKQXJ"]

                if self.quarter !=5 and self.cash<0:
                    self.reward -= 9999
                    done = True

                



        

        
        

        return self.get_state(), self.reward, done
    
    
class QLearning:
    def __init__(self, env, learning_rate=0.1, discount_factor=0.9, epsilon=0.1):
        self.env = env
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.epsilon = epsilon
        self.Q_table = {}

    def get_q_value(self, state, action):
        return self.Q_table.get((tuple(sorted(state.items())), tuple(sorted(action.items()))), 0.0)

    def update_q_value(self, state, action, reward, next_state):
        
        best_next_action = max([self.get_q_value(next_state, a) for a in self.env.action_space])
        self.Q_table[(tuple(sorted(state.items())), tuple(sorted(action.items())))] = self.get_q_value(state, action) + \
            self.learning_rate * (reward + self.discount_factor * best_next_action - self.get_q_value(state, action))

    def choose_action(self, state):
        if random.random() < self.epsilon:
            return random.choice(self.env.action_space)
        else:
            return max(self.env.action_space, key=lambda a: self.get_q_value(state, a))
    def save_model(self, filename):
        with open(filename, 'wb') as f:
            pickle.dump(self.Q_table, f)
    def load_model(self, filename):
        with open(filename, 'rb') as f:
            self.Q_table = pickle.load(f)

# 初始化环境
env = ERPSandbox()

# 初始化Q-learning
ql = QLearning(env)


# 定义动作空间
env.action_space = []


for factory_type in ErpInfo['factory']:
    env.action_space.append({'type': 'build_factory', 'factory_type': factory_type,'factory_buildType':'buy'})
    env.action_space.append({'type': 'build_factory', 'factory_type': factory_type,'factory_buildType':'rent'})
for factory_number in range(0,4):
    env.action_space.append({'type': 'buy_factory', 'factory_number': factory_number})
    env.action_space.append({'type': 'sell_factory', 'factory_number': factory_number})
for factory_number in range(0,4):
    for line_type in ErpInfo['production_line']:
        for product_choose in ErpInfo['product']:
            env.action_space.append({'type': 'build_new_production_line', 
                                    'factory_number': factory_number,
                                    'line_type':line_type,
                                    'product_choose':product_choose})
    for line_number in range(0,4):
        env.action_space.append({'type': 'sell_production_line','factory_number':factory_number,'line_number':line_number})
        env.action_space.append({'type': 'continue_build_production_line','factory_number':factory_number,'line_number':line_number})
        env.action_space.append({'type': 'produce','factory_number':factory_number,'line_number':line_number})
        for toProduct in ErpInfo['product']:
            env.action_space.append({'type': 'change_production_line','factory_number':factory_number,'line_number':line_number,'toProduct':toProduct})

for material in ErpInfo['material']:
    for num in range(1,9):
        env.action_space.append({'type': 'buy_material_normal','material':material,'num':num})
        env.action_space.append({'type': 'buy_material_emergency','material':material,'num':num})
for product in ErpInfo['product']:
    env.action_space.append({'type': 'research_product','product':product})
    
env.action_space.append({'type':'next_round'})

ql.load_model('ql.pkl')

# 训练Q-learning模型
num_episodes = 1000
save_step = 50
last_save = 0 
for episode in range(num_episodes):
    
    state = env.reset()
    done = False
    os.system('cls')
    while not done:
        action = ql.choose_action(state)
        next_state, theReward, done = env.step(action)
        ql.update_q_value(state, action, theReward, next_state)
        state = next_state
    if episode>(last_save+save_step):
        ql.save_model('ql.pkl')
        last_save=episode
# 输出训练后的Q表

from datetime import datetime
import colorama
import traceback
import sys
from functools import wraps
import random
import time
from faker import Faker


__all__ = ['retry','timer','user_agent','shell_color']



def user_agent():
	'''
		随机生成User-Agent

		返回值：
			字符串形式的User-Agent

	'''
	init = Faker()
	us = init.user_agent()
	return us



def retry(retries=0, timeout=1):
	'''
		程序发生错误后重试，并实时显示错误信息

		参数：
			retries：异常重试次数
			timeout：超时时间
		返回值：
			重试过程中成功 返回原函数的值
			重试后失败返回元组（False，错误信息）

	'''
	def decoeater(func):
		def warpper(*args,**kwds):
			trying = True
			n = 0  		# 统计重试次数
			while trying == True:
				try:
					result = func(*args,**kwds)
					trying = False
					return result       # 原函数成功直接返回 

				except Exception as e: 
					error = traceback.format_exc()
					print(error)  # 打印出详细的错误信息

					if retries > n:
						trying = True
						n += 1
						time.sleep(timeout)
					else:
						trying = False	 
						return trying,error 
		return warpper
	return decoeater



def timer(tips=None):
    '''
	    运行某个函数所需要的时间

	    参数：
	    	tips：提示信息，默认显示函数名
	    返回值：
	    	在控制台上打印出运行时间

    '''
    def warps(function):
        def function_timer(*args,**kwargs):
            t0 = datetime.now()
            result = function(*args, **kwargs)
            t1 = datetime.now()
            t = (t1 - t0).total_seconds()

            time_tip = ' finished in %s'%(t) + 's\n'
            if tips:
            	info = str(tips) + time_tip
            else:
                info = function.__name__ + '()' + time_tip
            print(info)
            return result
        return function_timer
    return warps



colorama.init(autoreset = True)
def shell_color(_str,color):
	'''
		控制台输出彩色的文本
		可用的颜色 ： red,green,yellow,blue,magenta,cyan,white
		注意： 调用的频率不宜过快（几毫秒级），否则程序会错

		参数：
			_str：需要渲染的字符串
			color：渲染的颜色
		返回值：
			经过渲染后的字符串

	'''
	
	Fore = colorama.Fore
	c_dic = {
				'r':Fore.RED,
				'g':Fore.GREEN,
				'y':Fore.YELLOW,
				'b':Fore.BLUE,
				'm':Fore.MAGENTA,
				'c':Fore.CYAN,
				'w':Fore.WHITE
				}
	color = c_dic.get(color,False)
	if color:
		c_str = color + _str + colorama.Style.RESET_ALL
		return c_str
	return _str
import time
import timeout_decorator

@timeout_decorator.timeout(5, timeout_exception=StopIteration)
def main():
    for i in range(1,10):
        time.sleep(1)
        print("{} seconds have passed".format(i))

try:
	main()
except:
	print('timeout!')
else:
	print('Success!')

print('end')
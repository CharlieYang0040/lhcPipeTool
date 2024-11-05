food = int(input('다음 세가지 중 고르시오\n1.감자, 2.옥수수, 3.수박\n: '))

if food == 1:
    food = '감자'
    price01 = 1000
    price02 = 2000
    price03 = 3000
    price = int(input(f'{price01}원 어치, {price02}원 어치, {price03}원 어치\n: '))



if food == 2:
    food = '옥수수'
    price01 = 4000
    price02 = 5000
    price03 = 6000
    price = int(input(f'{price01}원 어치, {price02}원 어치, {price03}원 어치\n: '))



if food == 3:
    food = '수박'
    price01 = 10000
    price02 = 20000
    price03 = 30000
    price = int(input(f'{price01}원 어치, {price02}원 어치, {price03}원 어치\n: '))




if price == 1:
    price = price01
if price == 2:
    price = price02
if price == 3:
    price = price03



print(f'{food} {price}원 어치를 선택하셨습니다')
amount = int(input('몇개를 주문하시겠습니까\n: '))
print(f'{price * amount}원')

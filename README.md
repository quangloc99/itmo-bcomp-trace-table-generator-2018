# ITMO BComp trace table generator
A simple script for generating trace table when doing lab work with the bcomp emulator written by my teacher. Now there is a newer version of bcomp, so I think I could publish my script, because it was cool :sunglasses:.

## Usage
Download the script as well as the `bcomp.jar` file. By default you should place them in the same folder, but this path to `bcomp.jar` can also be changed. Of course you need `python` and `java` installed.

For printing helps:
```
python3 tracetable-generator.py --help
```

## Example
```bash
$ python3 tracetable-generator.py > out.csv <<EOF
> ORG 00A
> BEGIN:
> CLA
> ADD X
> ADD Y
> MOV R
> HLT
> 
> ORG 03A
> X: WORD 0001
> Y: WORD 0002
> R: WORD ?
> EOF
$ cat out.csv
"Адр","Знчн","СК","РА","РК","РД","А","C","Адр_","Знчн_"
"00A","F200","00B","00A","F200","F200","0000","0","",""
"00B","403A","00C","03A","403A","0001","0001","0","",""
"00C","403B","00D","03B","403B","0002","0003","0","",""
"00D","303C","00E","03C","303C","0003","0003","0","03C","0003"
"00E","F000","00F","00E","F000","F000","0003","0","",""
```

The flag `-d` is also helpful to see the interaction on the fly. In the above example, when the flag `-d` is added, the following is printed:
```
Bcomp: Эмулятор Базовой ЭВМ. Версия r
Bcomp: Загружена исходная микропрограмма
Bcomp: Цикл прерывания начинается с адреса 90
Bcomp: БЭВМ готова к работе.
Bcomp: Используйте ? или help для получения справки
Client: ASM
Bcomp: Введите текст программы. Для окончания введите END
Client: ORG 00A

Client: BEGIN:

Client: CLA

Client: ADD X

Client: ADD Y

Client: MOV R

Client: HLT

Client: 

Client: ORG 03A

Client: X: WORD 0001

Client: Y: WORD 0002

Client: R: WORD ?

Client: END
Bcomp: Программа начинается с адреса 00A
Bcomp: Результат по адресу 03C
Client: 00a a
Bcomp: Адр Знчн  СК  РА  РК   РД    А  C Адр Знчн
Bcomp: 00A F200 00A 03B 0000 0002 0000 0
Client: flag 1
Bcomp: ВУ1: Флаг = 1 РДВУ = 00
Client: c
Bcomp: Адр Знчн  СК  РА  РК   РД    А  C Адр Знчн
Bcomp: 00A F200 00B 00A F200 F200 0000 0
Client: c
Bcomp: Адр Знчн  СК  РА  РК   РД    А  C Адр Знчн
Bcomp: 00B 403A 00C 03A 403A 0001 0001 0
Client: c
Bcomp: Адр Знчн  СК  РА  РК   РД    А  C Адр Знчн
Bcomp: 00C 403B 00D 03B 403B 0002 0003 0
Client: c
Bcomp: Адр Знчн  СК  РА  РК   РД    А  C Адр Знчн
Bcomp: 00D 303C 00E 03C 303C 0003 0003 0 03C 0003
Client: c
Bcomp: Адр Знчн  СК  РА  РК   РД    А  C Адр Знчн
Bcomp: 00E F000 00F 00E F000 F000 0003 0
Client: exit
```

The lines begins with `Client` is the input line for bcomp, and lines begins with `Bcomp` is the bcomp's responses.

## Limitations
- Can only works with VU1. It can be modified thought to work with other VU and also even input, but I was too lazy to do that.
- Cannot work with microcommand. But the same concept can be applied if you want to write your own version.

# Risc Machine. Экспериментальная модель процессора и транслятора

- Терновский Илья Евгеньевич, P3232
- alg -> asm | risc | neum | hw | tick -> instr | struct | stream | port | | prob1 | pipeline
- Упрощенный вариант (asm | risc | neum | hw | instr | struct | stream | port | pstr | prob1)

## Язык программирования

Синтаксис в расширенной БНФ.

```ebnf
<program> ::=  <section_data> <section_code> 

<section_data> ::= "." "data" { \n <data_definition> {<comment>} \n }
<section_code> ::= "." "code" { \n <instruction> {<comment>} \n }

<instruction> ::= "jmp" <label>
               | "jz" <label>
               | "jnz" <label>
               | "halt"
               | "move" <register> <operand>
               | "cmp" <register> <register>
               | "add" <register> <register> <register>
               | "sub" <register> <register> <register>
               | "mod" <register> <register> <register>
               | "load" <register> <address>
               | "store" <register> <address>
               | "in" <register>
               | "out" <register>
               | "inc" <register>
               | <label> ":"

<data_definition> ::= <identifier> <data_value>

<data_value> ::= <string>

<address> ::= $<identifier>

<register> ::= "r" <number>

<operand> ::= <register>
            | "#" <number>

<label> ::= <identifier>

<identifier> ::= <letter> { <letter> | <digit> }
         
<number> ::= <digit> { <digit> }

<string> ::= "\"" { <character> } "\""

<letter> ::= "a" | "b" | "c" | ... | "z"
           | "A" | "B" | "C" | ... | "Z"

<digit> ::= "0" | "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9"

<character> ::= <any printable ASCII character except quotation mark>

<comment> ::= ";" { <any printable ASCII character> }
```
В программе не может быть меток с одним названием, метки могут быть определены после использования.
Типизации не существует, все переменные трактуются как числа.

Код выполняется последовательно.

Команды:

- `load a, b` - загрузка из памяти значения по адресу `b` в регистр `a`, для указания значения из data используется `$`.
- `store a, b` - сохранение в память содержимого регистра `a` по адресу `b`.
- `add a, b, c` - сложение содержимого регистров `b`, `с`, и запись результата в регистр `a`.
- `sub a, b, c` - вычитание из регистра `b` регистра `с`, и запись результата в регистр `a`.
- `mod a, b, c` - остаток от деления регистра `b` на регистр `c`, и запись результата в регистр `a`.
- `inc a` - увеличение регистра `a` на 1.
- `cmp a, b` - выставление флагов по результату операции `a - b`.
- `halt` - остановка процессора.
- `in a` - запись значения в регистр `a` из порта 1.
- `out a` - вывод значения из памяти по регистру `a` в порт 1.
- `outn a` - вывод значения из регистра `a` (число которое лежит в регистре).
- `jz a` - переход на адрес `a`, если флаг `z` положительный.
- `jnz a` - переход на адрес `a`, если флаг `z` отрицательный.
- `jmp a` - переход на адрес `a`.
- `move a, b` - загрузка значения из регистра/прямое `b` в регистр `a`.

## Организация памяти
- Размер машинного слова не определен. Реализуется массивом словарей, одна команда\символ одна ячейка.

- Адресация абсолютная, адреса программы начинаются с 0, 
данные идут непосредственно со следующей ячейки после последней команды программы.

- Программисту доступно 8 регистров, адресуемых от r0 до r7.
Так же 200 ячеек под программу и данные (каждый символ данных занимает одну ячейку).

- Регистры связаны напрямую с памятью.
```text
           registers
+----------------------------+
| r0                         |
+----------------------------+
| r1                         |
+----------------------------+
| r2                         |
+----------------------------+
| r3                         |
+----------------------------+
| r4                         |
+----------------------------+
| r5                         |
+----------------------------+
| r6                         |
+----------------------------+
| r7                         |
+----------------------------+
| r8                         |
+----------------------------+

           memory
+----------------------------+
| 0 : op 0                   |
| 1 : op 1                   |
| ...                        |
| i : op i                   |
| i+1 const 1                |
| ...                        |
| i+k var 1                  |
| i+k+1 var 2                |
| ...                        |
+----------------------------+
```

- В ячейках 0-i хранятся команды программы.
- В ячейках i+1-i+k хранятся константы.
- В ячейках i+k+1-i+k+m хранятся переменные.
- Константы записываются в том же порядке, что и в секции data.
- Программист в праве записывать переменные вместо констант, на свой страх и риск.
- Текстовые данные занимают одну ячейку памяти на символ + ячейка для хранения длины.
- Числа записываются в ячейки памяти как есть.

По особенностям, так как программист напрямую управляет регистрами и памятью, стоит отметить только то, 
что статические данные из секции data инициализируются при загрузке программы и отображаются в память,
путем записи каждого символа в новую ячейку памяти, при этом одна ячейка до первого символа занимается длинной строки.

### Ввод вывод
- Реализован port mapped IO
- Ввод и вывод осуществляется через порт 1 (устанавливается по дефолту).
- Для ввода используется команда `in a`, для вывода `out a`, где `a` - регистр из или в который 
будет загружено значение из буфера порта.

```asm
CI при помощи Github Actions(тактически сворован с примера):

```yaml
name: Python CI

on:
  push:
    branches:
      - main

defaults:
  run:
    working-directory: ./

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: 3.11

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install poetry
          poetry install

      - name: Run tests and collect coverage
        run: |
          poetry run coverage run -m pytest .
          poetry run coverage report -m
        env:
          CI: true

  lint:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: 3.11

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install poetry
          poetry install

      - name: Check code formatting with Ruff
        run: poetry run ruff format --check .

      - name: Run Ruff linters
        run: poetry run ruff check .
```

где:

- `poetry` -- управления зависимостями для языка программирования Python.
- `coverage` -- формирование отчёта об уровне покрытия исходного кода.
- `pytest` -- утилита для запуска тестов.
- `ruff` -- утилита для форматирования и проверки стиля кодирования.

Пример использования и журнал работы процессора на примере программы:

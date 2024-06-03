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

Прямая работа с памятью невозможна, так как все данные хранятся в регистрах, и доступ к ним осуществляется через них.

### Ввод вывод

- Реализован port mapped IO
- Ввод и вывод осуществляется через порт 0 (устанавливается по дефолту).
- Для ввода используется команда `in a`, для вывода `out a`, где `a` - регистр из или в который
  будет загружено значение из буфера порта.

## Система команд

### Особенности процессора

- Поддерживаются только целочисленные операции.
- Поддерживаются строки, но только в качестве данных, которые затем будут представлены в виде чисел в памяти.
- Поддерживается 8 регистров (для решения поставленных задач не потребовалось больше), доступных для программы.
- Поддерживается 200 ячеек памяти для программы и данных.
- Поддерживаются команды ввода и вывода.
- Поток управления
    - Последовательное выполнение команд путем увеличения PC на 1 после каждой команды.
    - Условные переходы (jz, jnz), безусловные переходы (jmp), поддерживаются метки.
    - Остановка процессора (halt).

### Набор инструкций

- Команды однозначно транслируются в машинный код.
- Декодирование инструкции происходит за 1 такт.

Инструкции

| Инструкция | Кол-во тактов |
|:-----------|---------------|
| halt       | 0             |
| load       | 2             |
| store      | 2             |
| add        | 2             |
| sub        | 2             |
| mod        | 2             |
| inc        | 2             |
| cmp        | 2             |
| jz         | 1             |
| jnz        | 1             |
| jmp        | 1             |
| move       | 2 (1 direct)  |
| in         | 2             |
| out        | 2             |

### Кодирование инструкций

- Машинный код сериализуется в список JSON.
- Один элемент списка - одна инструкция.
  Пример:

```json
[
  {
    "index": 0,
    "opcode": "load",
    "args": [
      41,
      0,
      "data"
    ],
    "term": [
      1,
      null,
      "load"
    ]
  }
]
```

Где:

- `opcode` - строка с кодом операции;
- `args` - список аргументов команды, в данном случае: 41 - значение, 0 - регистр,
  "data" - обозначение о прямой записи значения;
- `index` - индекс команды в программе;
- `term` - список для упрощения отладки, в данном случае: 1 - строка с командой в секции code, null - метка в читаемом
  виде,
  "load" - строка с командой.

## Транслятор

Интерфейс командной строки: `translator.py <input_file>.zxc <target_file>`
Реализовано в модуле: [translator.py](./translator.py)

Программа принимает на вход файл с исходным кодом, при этом расширение должно быть обязательно .zxc,
так же принимает файл для записи машинного кода.

Он выполняет данные шаги:

1. Удаляет комментарии и пустые строки, для упрощения дальнейшей работы (функция `clean_source`).
2. Отделяет секцию data от code, что бы при обработке кода было проще подсчитывать номера команд.
   (функция `remove_data`).
3. Обрабатывает метки путем записи в словарь, что бы при обработке кода можно было использовать их.
   (функция `parse_labels`).
4. Обрабатывает секцию данных путем добавления данных в специальный список,
   который затем будет посимвольно отображен в память. (функция `parse_data`).
5. Транслирует исходный код в машинный код, при этом используя словарь меток и список данных. (функция `translate`).
6. Записывает машинный код в файл. (функция `write_code` из модуля `isa`).

### Правила трансляции
- Обязательное наличие секции data и code (могут быть пустыми).
- В секции data могут быть только строки вида `hello "hello world" 11` (pstr).
- Имена меток не должны повторяться.
- В секции code метки могут быть определены после использования.
- В секции code могут быть только команды из списка инструкций.
- При наличии данных в секции data, они будут записаны в память сразу после программы в порядке их следования.

## Модель процессора
Интерфейс командной строки:`machine.py <machine_code_file> <input_file>`
Реализовано в модуле: [machine.py](./machine.py)

### DataPath

![alt text](./resources/datapath.png)


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

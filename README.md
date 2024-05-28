# Risc Machine. Экспериментальная модель процессора и транслятора

- Терновский Илья Евгеньевич, P3232
- alg -> asm | risc | neum | hw | tick -> instr | struct | stream | port | | prob1 | pipeline
- Упрощенный вариант (asm | risc | neum | hw | instr | struct | stream | port | pstr | prob1)

## Язык программирования

Синтаксис в расширенной БНФ.

```ebnf
<program> ::= { <section> }

<section> ::= "section" "." "data" ":" { <data_definition> }
            | "section" "." "code" ":" { <instruction> }

<instruction> ::= "jmp" <label>
               | "jz" <label>
               | "jnz" <label>
               | "halt"
               | "move" <register> <register>
               | "cmp" <register> <register>
               | "add" <register> <register> <register>
               | "sub" <register> <register> <register>
               | "mod" <register> <register> <register>
               | "load" <register> <address>
               | "store" <register> <address>
               | "in" <register> <port number>
               | "out" <register> <port number>
               | "inc" <register>
               | <label> ":"
               | <comment>

<data_definition> ::= <identifier> <data_value>
                    | <comment>

<data_value> ::= <string>
               | <number>
               | "resb" <number>
               | <comment>

<address> ::= "(" <identifier> ")"
            | <identifier>

<register> ::= "r" <number>

<operand> ::= <register>
            | "#" <number>

<label> ::= "." <identifier>

<identifier> ::= <letter> { <letter> | <digit> }
              | <identifier> "." <identifier>

<number> ::= <digit> { <digit> }

<string> ::= "\"" { <character> } "\""

<letter> ::= "a" | "b" | "c" | ... | "z"
           | "A" | "B" | "C" | ... | "Z"

<digit> ::= "0" | "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9"

<character> ::= <any printable ASCII character except quotation mark>

<comment> ::= "@" { <any printable ASCII character> }
```

Команды:

- `load a, b` - загрузка из памяти значения по адресу `b` в регистр `a`.
- `store a, b` - сохранение в память содержимого регистра `a` по адресу `b`.
- `add a, b, c` - сложение содержимого регистров `b`, `с`, и запись результата в регистр `a`.
- `sub a, b, c` - вычитание из регистра `b` регистра `с`, и запись результата в регистр `a`.
- `mod a, b, c` - остаток от деления регистра `b` на регистр `c`, и запись результата в регистр `a`.
- `inc a` - увеличение регистра `a` на 1.
- `cmp a, b` - выставление флагов по результату операции `a - b`.
- `halt` - остановка модели.
- `in a` - запись значения в регистр `a`.
- `out a` - вывод значения из памяти по регистру `a`.
- `outn a` - вывод значения из регистра `a`.
- `jz a` - переход на адрес `a`, если флаг `z` положительный.
- `jnz a` - переход на адрес `a`, если флаг `z` отрицательный.
- `jmp a` - переход на адрес `a`.
- `move a, b` - загрузка значения из регистра/прямое `b` в регистр `a`.

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

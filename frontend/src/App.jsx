import { useEffect, useMemo, useState } from 'react';
import './App.css';

const operators = {
  '+': { precedence: 1, associativity: 'left', apply: (a, b) => a + b },
  '-': { precedence: 1, associativity: 'left', apply: (a, b) => a - b },
  '×': { precedence: 2, associativity: 'left', apply: (a, b) => a * b },
  '÷': {
    precedence: 2,
    associativity: 'left',
    apply: (a, b) => {
      if (b === 0) throw new Error('Cannot divide by zero');
      return a / b;
    },
  },
};

const keypad = [
  { label: 'AC', type: 'utility' },
  { label: '⌫', type: 'utility' },
  { label: '%', type: 'utility' },
  { label: '÷', type: 'operator' },
  { label: '7' },
  { label: '8' },
  { label: '9' },
  { label: '×', type: 'operator' },
  { label: '4' },
  { label: '5' },
  { label: '6' },
  { label: '-', type: 'operator' },
  { label: '1' },
  { label: '2' },
  { label: '3' },
  { label: '+', type: 'operator' },
  { label: '±', type: 'utility' },
  { label: '0' },
  { label: '.', type: 'utility' },
  { label: '=', type: 'equals' },
];

const isOperator = (value) => Object.hasOwn(operators, value);

function tokenize(expression) {
  const tokens = [];
  let index = 0;

  while (index < expression.length) {
    const char = expression[index];

    if (char === ' ') {
      index += 1;
      continue;
    }

    const previous = tokens[tokens.length - 1];
    const isUnaryMinus =
      char === '-' &&
      (!previous || previous.type === 'operator' || previous.type === 'open') &&
      /[\d.]/.test(expression[index + 1] || '');

    if (/\d/.test(char) || char === '.' || isUnaryMinus) {
      let rawNumber = isUnaryMinus ? '-' : '';
      index += isUnaryMinus ? 1 : 0;

      while (index < expression.length && /[\d.]/.test(expression[index])) {
        rawNumber += expression[index];
        index += 1;
      }

      if ((rawNumber.match(/\./g) || []).length > 1 || rawNumber === '.' || rawNumber === '-.') {
        throw new Error('Invalid number');
      }

      tokens.push({ type: 'number', value: Number(rawNumber) });
      continue;
    }

    if (isOperator(char)) tokens.push({ type: 'operator', value: char });
    else if (char === '(') tokens.push({ type: 'open', value: char });
    else if (char === ')') tokens.push({ type: 'close', value: char });
    else if (char === '%') tokens.push({ type: 'percent', value: char });
    else throw new Error('Invalid character');

    index += 1;
  }

  return tokens;
}

function toReversePolish(tokens) {
  const output = [];
  const stack = [];

  tokens.forEach((token) => {
    if (token.type === 'number') {
      output.push(token);
      return;
    }

    if (token.type === 'percent') {
      output.push(token);
      return;
    }

    if (token.type === 'operator') {
      const current = operators[token.value];

      while (stack.length > 0) {
        const top = stack[stack.length - 1];
        const topOperator = operators[top.value];

        if (
          top.type === 'operator' &&
          (topOperator.precedence > current.precedence ||
            (topOperator.precedence === current.precedence && current.associativity === 'left'))
        ) {
          output.push(stack.pop());
        } else {
          break;
        }
      }

      stack.push(token);
      return;
    }

    if (token.type === 'open') {
      stack.push(token);
      return;
    }

    if (token.type === 'close') {
      while (stack.length > 0 && stack[stack.length - 1].type !== 'open') {
        output.push(stack.pop());
      }

      if (stack.length === 0) throw new Error('Mismatched parentheses');
      stack.pop();
    }
  });

  while (stack.length > 0) {
    const token = stack.pop();
    if (token.type === 'open') throw new Error('Mismatched parentheses');
    output.push(token);
  }

  return output;
}

function evaluateExpression(expression) {
  const tokens = tokenize(expression);
  if (tokens.length === 0) return 0;

  const rpn = toReversePolish(tokens);
  const stack = [];

  rpn.forEach((token) => {
    if (token.type === 'number') {
      stack.push(token.value);
      return;
    }

    if (token.type === 'percent') {
      if (stack.length < 1) throw new Error('Invalid percent');
      stack.push(stack.pop() / 100);
      return;
    }

    if (token.type === 'operator') {
      if (stack.length < 2) throw new Error('Invalid expression');
      const right = stack.pop();
      const left = stack.pop();
      stack.push(operators[token.value].apply(left, right));
    }
  });

  if (stack.length !== 1 || !Number.isFinite(stack[0])) throw new Error('Invalid expression');
  return stack[0];
}

function formatNumber(value) {
  if (!Number.isFinite(value)) return 'Error';
  const precise = Number.parseFloat(value.toPrecision(12));
  return Object.is(precise, -0) ? '0' : String(precise);
}

function getCurrentNumber(expression) {
  return expression.match(/(?:^|[+\-×÷(])(-?\d*\.?\d*)$/)?.[1] || '';
}

function toggleSign(expression) {
  if (!expression) return '-';

  const wrappedNegative = expression.match(/\(-(\d+(?:\.\d*)?|\.\d+)\)$/);
  if (wrappedNegative) {
    return expression.slice(0, -wrappedNegative[0].length) + wrappedNegative[1];
  }

  const trailingNumber = expression.match(/(\d+(?:\.\d*)?|\.\d+)$/);
  if (!trailingNumber) return expression;

  const number = trailingNumber[1];
  const numberStart = expression.length - number.length;
  const maybeUnaryMinus = numberStart - 1;

  if (
    expression[maybeUnaryMinus] === '-' &&
    (maybeUnaryMinus === 0 || isOperator(expression[maybeUnaryMinus - 1]) || expression[maybeUnaryMinus - 1] === '(')
  ) {
    return expression.slice(0, maybeUnaryMinus) + number;
  }

  if (numberStart === 0) return `-${number}`;
  return `${expression.slice(0, numberStart)}(-${number})`;
}

function canCloseParenthesis(expression) {
  const opened = (expression.match(/\(/g) || []).length;
  const closed = (expression.match(/\)/g) || []).length;
  return opened > closed && !isOperator(expression.at(-1)) && expression.at(-1) !== '(';
}

export default function App() {
  const [expression, setExpression] = useState('');
  const [history, setHistory] = useState([]);
  const [status, setStatus] = useState('Ready');
  const [justSolved, setJustSolved] = useState(false);

  const preview = useMemo(() => {
    if (!expression || isOperator(expression.at(-1)) || expression.at(-1) === '(' || expression.at(-1) === '.') {
      return '';
    }

    try {
      return formatNumber(evaluateExpression(expression));
    } catch {
      return '';
    }
  }, [expression]);

  const display = expression || '0';

  const appendDigit = (digit) => {
    setExpression((current) => {
      if (justSolved) return digit;
      const number = getCurrentNumber(current);
      if (number === '0') return `${current.slice(0, -1)}${digit}`;
      if (number === '-0') return `${current.slice(0, -2)}-${digit}`;
      return `${current}${digit}`;
    });
    setStatus('Editing');
    setJustSolved(false);
  };

  const appendDecimal = () => {
    setExpression((current) => {
      if (justSolved || !current) return '0.';
      if (isOperator(current.at(-1)) || current.at(-1) === '(') return `${current}0.`;
      const number = getCurrentNumber(current);
      return number.includes('.') ? current : `${current}.`;
    });
    setStatus('Decimal mode');
    setJustSolved(false);
  };

  const appendOperator = (operator) => {
    setExpression((current) => {
      if (!current) return operator === '-' ? '-' : current;
      if (current.at(-1) === '.') return `${current.slice(0, -1)}${operator}`;
      if (isOperator(current.at(-1))) return `${current.slice(0, -1)}${operator}`;
      if (current.at(-1) === '(' && operator !== '-') return current;
      return `${current}${operator}`;
    });
    setStatus('Operator queued');
    setJustSolved(false);
  };

  const appendPercent = () => {
    setExpression((current) => {
      if (!current || isOperator(current.at(-1)) || current.at(-1) === '(' || current.at(-1) === '.') return current;
      return `${current}%`;
    });
    setStatus('Percent applied');
    setJustSolved(false);
  };

  const appendParenthesis = () => {
    setExpression((current) => {
      if (!current || isOperator(current.at(-1)) || current.at(-1) === '(') return `${current}(`;
      if (canCloseParenthesis(current)) return `${current})`;
      return `${current}×(`;
    });
    setStatus('Parenthesis balanced');
    setJustSolved(false);
  };

  const appendOpenParenthesis = () => {
    setExpression((current) => {
      if (!current || isOperator(current.at(-1)) || current.at(-1) === '(') return `${current}(`;
      return `${current}×(`;
    });
    setStatus('Parenthesis opened');
    setJustSolved(false);
  };

  const appendCloseParenthesis = () => {
    setExpression((current) => (canCloseParenthesis(current) ? `${current})` : current));
    setStatus('Parenthesis closed');
    setJustSolved(false);
  };

  const solve = () => {
    if (!expression) {
      setStatus('Enter a calculation');
      return;
    }

    try {
      const result = formatNumber(evaluateExpression(expression));
      setHistory((current) => [{ expression, result }, ...current].slice(0, 5));
      setExpression(result);
      setStatus('Solved');
      setJustSolved(true);
    } catch (error) {
      setStatus(error.message);
      setJustSolved(false);
    }
  };

  const clear = () => {
    setExpression('');
    setStatus('Ready');
    setJustSolved(false);
  };

  const backspace = () => {
    setExpression((current) => current.slice(0, -1));
    setStatus('Editing');
    setJustSolved(false);
  };

  const handleInput = (value) => {
    if (/^\d$/.test(value)) appendDigit(value);
    else if (value === '.') appendDecimal();
    else if (isOperator(value)) appendOperator(value);
    else if (value === '%') appendPercent();
    else if (value === '()') appendParenthesis();
    else if (value === '(') appendOpenParenthesis();
    else if (value === ')') appendCloseParenthesis();
    else if (value === '±') {
      setExpression((current) => toggleSign(current));
      setStatus('Sign toggled');
      setJustSolved(false);
    } else if (value === 'AC') clear();
    else if (value === '⌫') backspace();
    else if (value === '=') solve();
  };

  useEffect(() => {
    const onKeyDown = (event) => {
      const keyMap = {
        Enter: '=',
        '=': '=',
        Escape: 'AC',
        Backspace: '⌫',
        '*': '×',
        x: '×',
        X: '×',
        '/': '÷',
        '+': '+',
        '-': '-',
        '%': '%',
        '.': '.',
        '(': '(',
        ')': ')',
      };

      const nextValue = /^\d$/.test(event.key) ? event.key : keyMap[event.key];
      if (!nextValue) return;

      event.preventDefault();
      handleInput(nextValue);
    };

    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  });

  return (
    <main className="calculator-shell min-h-screen overflow-hidden px-4 py-6 text-stone-50 sm:px-6 lg:px-8">
      <div className="aurora aurora-one" />
      <div className="aurora aurora-two" />
      <div className="aurora aurora-three" />

      <section className="relative z-10 mx-auto flex min-h-[calc(100vh-3rem)] w-full max-w-6xl flex-col items-center justify-center gap-8 lg:flex-row lg:gap-14">
        <div className="intro-panel max-w-xl text-center lg:text-left">
          <p className="mb-4 inline-flex rounded-full border border-white/15 bg-white/10 px-4 py-2 text-xs font-bold uppercase tracking-[0.34em] text-amber-100 shadow-2xl shadow-black/20 backdrop-blur">
            Orbit Calc
          </p>
          <h1 className="text-balance text-5xl font-black leading-[0.9] tracking-[-0.08em] text-white sm:text-7xl">
            Fast math with a glassy pulse.
          </h1>
          <p className="mx-auto mt-6 max-w-lg text-base leading-8 text-stone-300 lg:mx-0">
            A responsive React calculator with keyboard input, live previews, percent math, decimals,
            sign toggling, chained operations, and a compact calculation history.
          </p>

          <div className="mt-8 grid grid-cols-3 gap-3 text-left">
            {['Keyboard ready', 'Safe parser', 'Mobile first'].map((item) => (
              <div className="stat-card rounded-3xl border border-white/10 bg-white/[0.07] p-4 backdrop-blur" key={item}>
                <span className="block text-2xl font-black text-amber-200">✓</span>
                <span className="mt-2 block text-xs font-semibold uppercase tracking-[0.18em] text-stone-300">
                  {item}
                </span>
              </div>
            ))}
          </div>
        </div>

        <div className="calculator-card relative w-full max-w-md rounded-[2rem] border border-white/15 bg-zinc-950/70 p-4 shadow-[0_30px_100px_rgba(0,0,0,0.55)] backdrop-blur-2xl sm:p-5">
          <div className="glow-ring" />

          <div className="screen relative overflow-hidden rounded-[1.6rem] border border-white/10 bg-black/45 p-5 shadow-inner">
            <div className="mb-8 flex items-center justify-between text-xs uppercase tracking-[0.28em] text-stone-400">
              <span>{status}</span>
              <span>Rad</span>
            </div>

            <div className="min-h-24">
              <div className="expression-display break-words text-right text-4xl font-black tracking-[-0.05em] text-white sm:text-5xl">
                {display}
              </div>
              <div className="mt-3 h-7 text-right text-lg font-semibold text-amber-200">
                {preview && preview !== expression ? `= ${preview}` : ''}
              </div>
            </div>
          </div>

          <div className="mt-4 grid grid-cols-4 gap-3">
            <button className="calc-key key-utility" type="button" onClick={() => handleInput('()')}>
              ()
            </button>
            {keypad.map((key) => (
              <button
                className={`calc-key ${key.type === 'operator' ? 'key-operator' : ''} ${
                  key.type === 'utility' ? 'key-utility' : ''
                } ${key.type === 'equals' ? 'key-equals' : ''}`}
                key={key.label}
                type="button"
                onClick={() => handleInput(key.label)}
              >
                {key.label}
              </button>
            ))}
          </div>

          <div className="history-panel mt-4 rounded-[1.4rem] border border-white/10 bg-white/[0.06] p-4">
            <div className="mb-3 flex items-center justify-between text-xs uppercase tracking-[0.24em] text-stone-400">
              <span>History</span>
              <button className="text-amber-200 transition hover:text-white" type="button" onClick={() => setHistory([])}>
                Clear
              </button>
            </div>

            <div className="history-scroll flex max-h-32 flex-col gap-2 overflow-y-auto pr-1">
              {history.length === 0 ? (
                <p className="text-sm text-stone-500">Solved calculations appear here.</p>
              ) : (
                history.map((item, index) => (
                  <button
                    className="history-item rounded-2xl bg-black/20 px-3 py-2 text-left transition hover:bg-white/10"
                    key={`${item.expression}-${index}`}
                    type="button"
                    onClick={() => {
                      setExpression(item.result);
                      setStatus('Restored from history');
                      setJustSolved(true);
                    }}
                  >
                    <span className="block truncate text-xs text-stone-400">{item.expression}</span>
                    <span className="block truncate text-sm font-bold text-white">= {item.result}</span>
                  </button>
                ))
              )}
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}

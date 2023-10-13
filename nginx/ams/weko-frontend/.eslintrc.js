module.exports = {
  env: {
    browser: true,
    node: true
  },
  extends: ['plugin:vue/vue3-recommended', 'eslint:recommended', '@vue/prettier', '@nuxtjs/eslint-config-typescript'],
  parserOptions: {
    parser: '@typescript-eslint/parser',
    ecmaVersion: 'latest',
    sourceType: 'module',
    requireConfigFile: false
  },
  plugins: ['@typescript-eslint', 'vue', 'import'],
  rules: {
    semi: ['error', 'always'],
    'semi-spacing': ['error', { after: true, before: false }],
    'semi-style': ['error', 'last'],
    'no-extra-semi': 'error',
    'no-unexpected-multiline': 'error',
    'no-unreachable': 'error',
    'import/no-duplicates': 'error',
    'import/order': [
      'error',
      {
        alphabetize: {
          order: 'asc'
        },
        groups: ['builtin', 'external', 'internal', 'parent', 'sibling', 'index', 'object', 'type'],
        'newlines-between': 'always'
      }
    ],
    'vue/singleline-html-element-content-newline': 'off',
    'vue/multiline-html-element-content-newline': 'off',
    'vue/multi-word-component-names': 'off',
    'vue/html-closing-bracket-spacing': 'off',
    'vue/html-closing-bracket-newline': [
      'error',
      {
        singleline: 'never',
        multiline: 'never'
      }
    ],
    'vue/html-self-closing': [
      'error',
      {
        html: {
          void: 'always'
        }
      }
    ],
    'space-before-function-paren': [
      'error',
      {
        anonymous: 'always',
        named: 'never',
        asyncArrow: 'always'
      }
    ],
    'vue/attribute-hyphenation': 'off',
    'vue/html-indent': 'off'
  },
  root: true
};

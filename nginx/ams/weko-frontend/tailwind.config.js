module.exports = {
  content: [
    './components/**/*.{vue,js,jsx,ts,tsx}',
    './layouts/**/*.vue',
    './pages/**/*.vue',
    './node_modules/flowbite/**/*.{js,ts}'
  ],
  theme: {
    extend: {
      colors: {
        'miby-black': '#333333',
        'miby-blue': '#071A46',
        'miby-light-blue': '#6582A4',
        'miby-dark-blue': '#051334',
        'miby-link-blue': '#5B7593',
        'miby-gray': '#DFE0E2',
        'miby-dark-gray': '#999999',
        'miby-border-gray': '#EEEEEE',
        'miby-border-black': '#24272B',
        'miby-bg-gray': '#FCFCFC',
        'miby-light-gray': '#F2F2F2',
        'miby-thin-gray': '#CCCCCC',
        'miby-faq-gray': '#555555',
        'miby-orange': '#DB6915',
        'miby-purple': '#E7E2F2',
        'miby-thin-green': '#A6ADA0',
        'miby-tag-gray': '#AFAFAF',
        'miby-tag-yellow': '#C9C2B1',
        'miby-tag-orange': '#B9AFA8',
        'miby-tag-white': '#F1F1F1',
        'miby-searchtags-blue': '#DCE2ED',
        'miby-form-red': '#DB1515',
        'miby-mobile-gray': '#707070',
        'miby-mobile-blue': '#061435',
        'miby-header-blue': '#040E27'
      },
      fontFamily: {
        notoSerif: ['Noto Serif JP', '"Noto Sans"'],
        notoSans: ['"Noto Sans JP"']
      },
      backgroundImage: {
        MainBg: "url('/img/ams/kv.jpg')"
      },
      padding: {
        6.5: '25px',
        7.5: '30px',
        14.5: '58px',
        15: '60px',
        32.5: '130px'
      },
      margin: {
        6.5: '25px',
        7.5: '30px',
        14.5: '58px',
        15: '60px'
      }
    }
  },
  plugins: [require('flowbite/plugin'), require('daisyui')]
};

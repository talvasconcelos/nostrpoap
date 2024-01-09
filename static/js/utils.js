function loadTemplateAsync(path) {
    const result = new Promise(resolve => {
      const xhttp = new XMLHttpRequest()
  
      xhttp.onreadystatechange = function () {
        if (this.readyState == 4) {
          if (this.status == 200) resolve(this.responseText)
  
          if (this.status == 404) resolve(`<div>Page not found: ${path}</div>`)
        }
      }
  
      xhttp.open('GET', path, true)
      xhttp.send()
    })
  
    return result
  }

  
  function satOrBtc(val, showUnit = true, showSats = false) {
    const value = showSats
      ? LNbits.utils.formatSat(val)
      : val == 0
        ? 0.0
        : (val / 100000000).toFixed(8)
    if (!showUnit) return value
    return showSats ? value + ' sat' : value + ' BTC'
  }
  
  function isValidKey(key, prefix = 'n') {
    try {
      if (key && key.startsWith(prefix)) {
        let { _, data } = NostrTools.nip19.decode(key)
        key = data
      }
      return isValidKeyHex(key)
    } catch (error) {
      return false
    }
  }
  
  function isValidKeyHex(key) {
    return key?.toLowerCase()?.match(/^[0-9a-f]{64}$/)
  }
  
  function formatCurrency(value, currency) {
    return new Intl.NumberFormat(window.LOCALE, {
      style: 'currency',
      currency: currency
    }).format(value)
  }
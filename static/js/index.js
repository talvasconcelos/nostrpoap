const issuer = async () => {
  Vue.component(VueQrcode.name, VueQrcode)

  await keyPair('static/components/key-pair/key-pair.html')
  await issuerDetails('static/components/issuer-details/issuer-details.html')

  const nostr = window.NostrTools

  const mapAwards = obj => {
    obj.date = Quasar.utils.date.formatDate(
      new Date(obj.time * 1000),
      'YYYY-MM-DD HH:mm'
    )
    return obj
  }

  new Vue({
    el: '#vue',
    mixins: [windowMixin],
    delimiters: ['${', '}'],
    data: function () {
      return {
        issuer: {},
        poaps: [],
        poapsTable: {
          columns: [
            {name: 'id', align: 'left', label: 'ID', field: 'id'},
            {name: 'name', align: 'left', label: 'Name', field: 'name'},
            {
              name: 'wallet',
              align: 'left',
              label: 'Wallet',
              field: 'wallet'
            }
          ],
          pagination: {
            rowsPerPage: 10
          }
        },
        importKeyDialog: {
          show: false,
          data: {
            privateKey: null
          }
        },
        showKeys: false,
        endpoint: `/poap/api/v1/issuer`,
        options: [
          {
            type: 'str',
            description: 'A display name for the badge',
            name: 'name'
          },
          {
            type: 'str',
            description: 'A small description for the badge',
            name: 'description'
          },
          {
            type: 'str',
            description: 'Image URL for the badge',
            name: 'image'
          },
          {
            type: 'str',
            description: 'Thumbnail URL for the badge',
            name: 'thumbs'
          }
        ],
        formDialog: {
          show: false,
          data: {}
        },
        urlDialog: {
          show: false,
          data: {}
        }
      }
    },
    computed: {},
    methods: {
      generateKeys: async function () {
        const privateKey = nostr.generatePrivateKey()
        await this.createIssuer(privateKey)
      },
      importKeys: async function () {
        this.importKeyDialog.show = false
        let privateKey = this.importKeyDialog.data.privateKey
        if (!privateKey) {
          return
        }
        try {
          if (privateKey.toLowerCase().startsWith('nsec')) {
            privateKey = nostr.nip19.decode(privateKey).data
          }
        } catch (error) {
          this.$q.notify({
            type: 'negative',
            message: `${error}`
          })
        }
        await this.createIssuer(privateKey)
      },
      showImportKeysDialog: async function () {
        this.importKeyDialog.show = true
      },
      async createIssuer(privateKey) {
        try {
          const pubkey = nostr.getPublicKey(privateKey)
          const payload = {
            private_key: privateKey,
            public_key: pubkey
          }
          const {data} = await LNbits.api.request(
            'POST',
            '/poap/api/v1/issuer',
            this.g.user.wallets[0].adminkey,
            payload
          )
          this.issuer = data
          this.$q.notify({
            type: 'positive',
            message: 'Issuer Created!'
          })
        } catch (error) {
          LNbits.utils.notifyApiError(error)
        }
      },
      async getIssuer() {
        try {
          const {data} = await LNbits.api.request(
            'GET',
            '/poap/api/v1/issuer',
            this.g.user.wallets[0].inkey
          )
          this.issuer = data
          return data
        } catch (error) {
          LNbits.utils.notifyApiError(error)
        }
      },
      toggleIssuerKeys(value) {
        this.showKeys = value
      },
      handleIssuerDeleted() {
        this.issuer = null
        this.showKeys = false
      },
      closeFormDialog() {
        this.formDialog.show = false
        this.formDialog.data = {}
      },
      async getPoaps() {
        try {
          const {data} = await LNbits.api.request(
            'GET',
            '/poap/api/v1/poaps',
            this.g.user.wallets[0].inkey
          )
          this.poaps = [...data]
          console.log(this.poaps)
        } catch (error) {
          LNbits.utils.notifyApiError(error)
        }
      },
      async createPoap() {
        try {
          const data = this.formDialog.data
          const {poap} = await LNbits.api.request(
            'POST',
            '/poap/api/v1/poaps',
            this.g.user.wallets[0].adminkey,
            data
          )
          this.poaps = [...this.poaps, poap]
          this.closeFormDialog()
        } catch (error) {
          LNbits.utils.notifyApiError(error)
        }
      },

      exportCSV: function () {
        LNbits.utils.exportCSV(this.poapsTable.columns, this.poaps)
      },
      openformDialog(id) {
        const [poapId, itemId] = id.split(':')
        const poap = _.findWhere(this.poaps, {id: poapId})
        if (itemId) {
          const item = poap.itemsMap.get(id)
          this.formDialog.data = {
            ...item,
            poap: poapId
          }
        } else {
          this.formDialog.data.poap = poapId
        }
        this.formDialog.data.currency = poap.currency
        this.formDialog.show = true
      }
    },
    async created() {
      await this.getIssuer()
      if (this.g.user.wallets.length) {
        await this.getPoaps()
      }
    }
  })
}

issuer()

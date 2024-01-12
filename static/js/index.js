const issuer = async () => {
  Vue.component(VueQrcode.name, VueQrcode)

  await keyPair('static/components/key-pair/key-pair.html')
  await issuerDetails('static/components/issuer-details/issuer-details.html')
  await poapList('static/components/poap-list/poap-list.html')

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
              name: 'image',
              align: 'left',
              label: 'Image',
              field: 'image'
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
          this.poaps = [...data].map(mapPoaps)
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
      openFormDialog(id) {
        const poap = this.poaps.find(p => p.id === id)
        this.formDialog.data = poap
        this.formDialog.show = true
      }
    },
    async created() {
      await this.getIssuer()
      if (this.issuer.id) {
        await this.getPoaps()
      }
    }
  })
}

issuer()

// pub: 38f0d5d4504ca0eef6b7435881e499371fb27ca7812cd9bff3e7ee6857a40480
// sec: 8b9c563736267486f467572a297d19012f468c83713fabb70baa6458e45dc0cc

// https://image.nostr.build/ae692f0d98c29e90dbea194608858f078e16d94b2d2bf90e85456e23026bc537.jpg
// https://image.nostr.build/237bf04594f02e4a03d752b4f74adf587998cb5ed23acd7610c73c274acd93c9.jpg

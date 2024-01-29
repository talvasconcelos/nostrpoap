async function issuerDetails(path) {
  const template = await loadTemplateAsync(path)
  Vue.component('issuer-details', {
    name: 'issuer-details',
    props: ['issuer-id', 'adminkey', 'inkey', 'show-keys'],
    template,

    data: function () {
      return {}
    },
    methods: {
      toggleIssuerKeys: async function () {
        this.$emit('show-keys', !this.showKeys)
      },

      republishIssuerData: async function () {
        try {
          await LNbits.api.request(
            'PUT',
            `/poap/api/v1/issuer/${this.issuerId}/nostr`,
            this.adminkey
          )
          this.$q.notify({
            type: 'positive',
            message: 'Issuer data republished to Nostr',
            timeout: 5000
          })
        } catch (error) {
          console.warn(error)
          LNbits.utils.notifyApiError(error)
        }
      },
      requeryIssuerData: async function () {
        try {
          await LNbits.api.request(
            'GET',
            `/poap/api/v1/merchant/${this.issuerId}/nostr`,
            this.adminkey
          )
          this.$q.notify({
            type: 'positive',
            message: 'Merchant data refreshed from Nostr',
            timeout: 5000
          })
        } catch (error) {
          console.warn(error)
          LNbits.utils.notifyApiError(error)
        }
      },
      deleteIssuerTables: function () {
        LNbits.utils
          .confirmDialog(
            `
             POAPs and awards will be deleted also!
             Are you sure you want to delete this issuer?
            `
          )
          .onOk(async () => {
            try {
              await LNbits.api.request(
                'DELETE',
                '/poap/api/v1/issuer/' + this.issuerId,
                this.adminkey
              )
              this.$emit('issuer-deleted', this.issuerId)
              this.$q.notify({
                type: 'positive',
                message: 'Issuer Deleted',
                timeout: 5000
              })
            } catch (error) {
              console.warn(error)
              LNbits.utils.notifyApiError(error)
            }
          })
      },
      deleteMerchantFromNostr: function () {
        LNbits.utils
          .confirmDialog(
            `
             Do you want to remove the merchant from Nostr?
            `
          )
          .onOk(async () => {
            try {
              await LNbits.api.request(
                'DELETE',
                `/nostrmarket/api/v1/merchant/${this.issuerId}/nostr`,
                this.adminkey
              )
              this.$q.notify({
                type: 'positive',
                message: 'Merchant Deleted from Nostr',
                timeout: 5000
              })
            } catch (error) {
              console.warn(error)
              LNbits.utils.notifyApiError(error)
            }
          })
      }
    },
    created: async function () {}
  })
}

App = {
    loading: false,
    web3Provider: null,
    contracts: {},

    load: async () => {
      await App.initWeb3();
      await App.initContract();
      await App.checkLogin();

    },

    initWeb3:  async () => {

      if(window.web3) {
        App.web3Provider = window.web3.currentProvider;
        console.log('Metamask Available');
      }
      else {
        App.web3Provider = new Web3.providers.HttpProvider('http://localhost:8545');
        console.log('Ganache Available');
      }

      web3 = new Web3(App.web3Provider);
    },

    initContract:  async () => {

      $.getJSON('Bank.json',function(data){

        var bankArtifact = data;
        App.contracts.bank = TruffleContract(bankArtifact);
        App.contracts.bank.setProvider(App.web3Provider);
      });
      
    },

    checkLogin:  async () => {

      value = parseInt(localStorage.login);
      console.log(value);

      if(value == 0)
      {
        alert('You are not logged in !!')
        window.location.href = "login.html"
      }
      return App.bindEvents();
    },

    bindEvents: function() {

      $(document).on('click', '.btn-showtransactions', App.showTransactions);
      $(document).on('click', '.btn-checkBalance', App.getBalance);
    },  

    getBalance:function(event) {

    const u = localStorage.account;
    const user = parseInt(u);
    console.log(user);

    var bankInstance;

    web3.eth.getAccounts(function(error,accounts){

      if(error) {
        console.log(error);
      }

      var account=accounts[0];
      console.log(account);

      App.contracts.bank.deployed().then(function(instance){
        
        bankInstance=instance;
        return bankInstance.getBalance(user,{from:account});

      }).then(function(result){

        const balance=(result.toNumber());
        $('#bal').html(balance);

        var delayInMilliseconds = 3000; 

        setTimeout(function() {
          $('#bal').html('*****');
         }, delayInMilliseconds);
      }).catch(function(err){
        console.log(err.message);
      });

    });
   },

   showTransactions: function(event) {

    const user = parseInt(localStorage.account);
    var bankInstance;

    web3.eth.getAccounts(function(error,accounts){

      if(error) {
        console.log(error);
      }

      var account=accounts[0];
      console.log(account);

      App.contracts.bank.deployed().then(function(instance){
        
        bankInstance=instance;
        return bankInstance.accounts(user,{from:account});

      }).then(function(result){
        
        const count = result[8].toNumber();
        console.log(count);
        var t="";
        for(let i = count - 1;i >= 0;i--)
        {
          let r1;
          let s1;
          let r2;
          let a1;
          App.contracts.bank.deployed().then(function(instance){
            bankInstance=instance;
            return bankInstance.getRole(user,i,{from:account});
          }).then(function(result1){
            
            const role = result1;
            r1=role;
            
            console.log(r1);
            App.contracts.bank.deployed().then(function(instance){
              bankInstance=instance;
              return bankInstance.getSender(user,i,{from:account});
            }).then(function(result2){
              const sender = result2.toNumber();
              s1=parseInt(sender);
              console.log(sender);
              
              App.contracts.bank.deployed().then(function(instance){
                bankInstance=instance;
                return bankInstance.getRecipient(user,i,{from:account});
              }).then(function(result3){
                const recipient = result3.toNumber();
                r2=parseInt(recipient);
                console.log(r2);
                
                App.contracts.bank.deployed().then(function(instance){
                  bankInstance=instance;
                  return bankInstance.getAmount(user,i,{from:account});
                }).then(function(result4){
                  const amount = result4.toNumber();
                  a1=parseInt(amount);
                  console.log(a1);
                  
                  console.log(t);
                  t="";
                  t+="<tr>";
                  t+="<td>"+r1+"</td>";
                  t+="<td>"+s1+"</td>";
                  t+="<td>"+r2+"</td>";
                  t+="<td>"+a1+"</td></tr>";
                  document.getElementById('list').innerHTML +=t;
                  const button=document.getElementById('madhu1');
                  button.disabled=true;
                }).catch(function(err){
                  console.log(err.message);
                });
              }).catch(function(err){
                console.log(err.message);
              });
            }).catch(function(err){
              console.log(err.message);
            });
          }).catch(function(err){
            console.log(err.message);
          });
        }  
       
      }).catch(function(err){
        console.log(err.message);
      });

    });

  }
}

$(() => {
  $(window).load(() => {
    App.load()
  })
})
App={

	web3Provider: null,
	contracts: {},

	init: async function() {

		return await App.initWeb3();
	},

	initWeb3: async function() {

		if(window.web3) {
			App.web3Provider = window.web3.currentProvider;
			console.log('Metamask Available');
		}
		else {
			App.web3Provider = new Web3.providers.HttpProvider('http://localhost:8545');
			console.log('Ganache Available');
		}

		web3 = new Web3(App.web3Provider);
		return App.initContract();
	},

	initContract: function() {

		$.getJSON('Bank.json',function(data){

			var bankArtifact = data;
			App.contracts.bank = TruffleContract(bankArtifact);
			App.contracts.bank.setProvider(App.web3Provider);
		});
			return App.bindEvents();
	},

	bindEvents: function() {

		$(document).on('click', '.btn-login', App.loginUser);
	},

	loginUser: function(event) {
		event.preventDefault();

		var bankInstance;
		
		var username = document.getElementById('username').value;
		var password = document.getElementById('password').value;

		const user = parseInt(username);

		console.log(username,password);
		

		web3.eth.getAccounts(function(error,accounts){

			if(error) {
				console.log(error);
			}

			var account=accounts[0];
			console.log(account);

			App.contracts.bank.deployed().then(function(instance){
				
				bankInstance=instance;
				return bankInstance.loginAccount(user, password,{from:account});

			}).then(function(result){

				console.log(result);
				if(parseInt(result)==1) {

					localStorage.account = user;
					localStorage.login = "1";
          			window.location.href = "dashboard.html"
				}
				
				else {
					alert('Wrong Credentials, try again');
					window.location.reload();
				}

			}).catch(function(err){
				console.log(err.message);
			});

		});
	}
}

$(function() {
  $(window).load(function() {
    App.init();
  });
});
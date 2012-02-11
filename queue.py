# -*- coding: utf-8 -*-
# 10/02/2012 - Add variables to beginners.ini
#written by rohezal, who is even worse then old in python
#Description: allows report a player by giving match id
#Global Admin function who can globally ingame for 2 days
import re
import math
import time
import ConfigParser
import threading
import os
import httplib, urllib
from MasterServer import MasterServer
from PluginsManager import ConsolePlugin
from S2Wrapper import Savage2DaemonHandler

class queue(ConsolePlugin):
	VERSION = "0.0.1"
	modlist = []
	#name desc minplayers maxplayers ip currentPlayers
	modVar1 = ["Spell_HailStorm_AnimName", "Spell_HailStorm_CastEffectPath", "Spell_HailStorm_AmmoCount", "Spell_HailStorm_AnimChannel", "Spell_HailStorm_CursorPath", "Spell_HailStorm_CastTime"]
	modVar2 = ["Spell_HailStorm_Description", "Spell_HailStorm_GadgetName", "Spell_HailStorm_CooldownOnDamage", "Spell_HailStorm_CooldownTime", "Spell_HailStorm_Name", "Spell_HailStorm_Cost"]
	modVar3 = ["Spell_HailStorm_IconPath", "Spell_HailStorm_HoldEffect", "Spell_HailStorm_ImpactTime", "Spell_HailStorm_InitialAmmo", "Spell_HailStorm_ImpactEffectPath", "Spell_HailStorm_ManaCost"]
	modVar4 = ["Spell_HailStorm_Model1Bone", "Spell_HailStorm_Model1Path", "Spell_HailStorm_MaxDeployable", "Spell_HailStorm_MinRange", "Spell_HailStorm_Model2Bone", "Spell_HailStorm_Range"]
	modVar5 = ["Spell_HailStorm_Model2Path", "Spell_HailStorm_TargetMaterialPath", "Spell_HailStorm_SnapcastBreakAngle", "Spell_HailStorm_SpeedMult", "Spell_HailStorm_VoiceTipPath", "Spell_HailStorm_TargetStateDuration"]
	modVars = [modVar1,modVar2,modVar3,modVar4,modVar5]
	resetUpdate = 1
	modsLoaded = 0
	playerlist = []
	playerqueue = [] 
	isModServer = 0 #read from config
	isModServerGameVar = "Spell_HailStorm_TargetRadius" #shows the user if he is on a mod server. if true disable join gui
	isModServerCurrentMod = "survival" #read from config

	matchid = 0
	matchidVar = "Entity_NpcController_Description" 

	def getMatchID(self, *args, **kwargs):
		print('Python In getMatchID')
		queue.matchid = args[0]
		print('Python getMatchID was called with matchid ' + str(queue.matchid))
		kwargs['Broadcast'].broadcast("set " + str(queue.matchidVar) + " " + str(queue.matchid))

	def onPluginLoad(self, config):
		print ("In Plugin Load")
		self.ms = MasterServer ()
		ini = ConfigParser.ConfigParser()
		ini.read(config)
		for (name, value) in ini.items('queue'):
			print ("In ini Loop: " + str(name) + " / " + str(value) )
			if (name == "ismodserver"):
				print ("In: if (name == isModServer):")
				queue.isModServer = value
			if (name == "ismodservercurrentmod"):
				print ("In: if (name == isModServerCurrentMod)")
				queue.isModServerCurrentMod = value

		print ("Setting: " + "Set " + str(queue.isModServerGameVar) + " " + str(queue.isModServer))
		print ("isModServerCurrentMod: " + queue.isModServerCurrentMod)
		#kwargs['Broadcast'].broadcast("Set " + str(queue.isModServerGameVar) + " " + str(queue.isModServer))	

	def onPhaseChange(self, *args, **kwargs):
		phase = int(args[0]) #phase7 is gameends
		if (phase == 7): 
			queue.modsLoaded = 0
			queue.resetUpdate = 1 #make sure there is no writing to the mod list while its being rebuilded
		if (queue.modsLoaded == 0):
			queue.modsLoaded = 1
			self.getMods()
			self.storeModsInGameVars(kwargs)
			queue.resetUpdate = 0

	def updatePlayerNumbers(self, *args, **kwargs):
		while (1 == 1):
			time.sleep(10)
			if (queue.resetUpdate == 0):
				self.updateModPlayers()
				self.updateModPlayersGameVars(**kwargs)
				self.checkModTreshold(**kwargs)


	def onMessage(self, *args, **kwargs):

		#on a mod server the client can just play and not join queues.

		if (int(queue.isModServer) == 1):
			return

		else:
			name = args[1]
			message = args[2]

			modinfo = re.match("GetMod (\d+)", message, flags=re.IGNORECASE)
			modjoin = re.match("joinMod (\S+)", message, flags=re.IGNORECASE)								
			#modleave = re.match("leaveMod (\S+)", message, flags=re.IGNORECASE)
			modleave = re.match("leaveMod", message, flags=re.IGNORECASE)																

			test_startgame = re.match("startgame", message, flags=re.IGNORECASE)																

			if test_startgame:				
				kwargs['Broadcast'].broadcast('startgame')

			if modinfo:
				print "Modinfo: " + modinfo.group(1)
				#client = self.getPlayerByName(name)
				modnumber = int (modinfo.group(1))
				if (modnumber > (len(queue.modlist)-1)):
					modnumber = 0
				reason = "Name: " + queue.modlist[modnumber][0] + " / Desc: " + queue.modlist[modnumber][1] + " / Minplayer: " + str(queue.modlist[modnumber][2]) + " / Maxplayer: " + str(queue.modlist[modnumber][3]) + " / Ip: " + str(queue.modlist[modnumber][4]) + "" + str(queue.modlist[modnumber][5])
				kwargs['Broadcast'].broadcast("SendMessage -1 \"%s\"" % (reason))

			if modjoin:
				localJoinList = [name, modjoin.group(1)]
				#self.joinQueue(localJoinList, **kwargs)
				self.joinQueue(localJoinList)

			if modleave:
				#localLeaveList = [name, modleave.group(1)]
				#self.leaveQueue(localLeaveList, **kwargs)
				#self.leaveQueue(localLeaveList)
				self.leaveQueue(name)



	def storeModsInGameVars(self, *args, **kwargs):
		i = 0
		for var_entry in queue.modVars:
			if ((len(queue.modlist)-1) < i): #make sure we do not read more mods then exist to write them in to game variables
				break
				
			kwargs['Broadcast'].broadcast("Set " + queue.modVars[i][0] + " " + queue.modlist[i][0])	
			kwargs['Broadcast'].broadcast("Set " + queue.modVars[i][1] + " " + queue.modlist[i][1])	
			kwargs['Broadcast'].broadcast("Set " + queue.modVars[i][2] + " " + queue.modlist[i][2])	
			kwargs['Broadcast'].broadcast("Set " + queue.modVars[i][3] + " " + queue.modlist[i][3])	
			kwargs['Broadcast'].broadcast("Set " + queue.modVars[i][4] + " " + queue.modlist[i][4])	
			kwargs['Broadcast'].broadcast("Set " + queue.modVars[i][5] + " " + queue.modlist[i][5])	
			i=i+1

	# we loop through players. we check for each player which mod he wants to join. if the mod has enough (waiting) players connect to the server in inner loop 
	def checkModTreshold(self, *args, **kwargs):
		print "In checkModTreshold\n" ;
		for player in queue.playerlist:
			print player
			print "\n"
			if( len(player['mod']) > 0): #player has joined a mod
				print "Player joined a mod. Its: " + player['mod'] +". Now we should see the mod iteration\n"
				for mod in queue.modlist:
					print "In Mod Iteration\n"
					print mod[0]
					print "We should saw mod. If: " + mod[0] + " == " + player['mod'] + "\n"
					#name desc minplayers maxplayers ip currentPlayers
					if(mod[0] == player['mod']):
						print "In if: " + mod[2] + " <= " + mod[5] + "\n"
						if(mod[2] <= mod[5]):
							print "ClientExecScript "+player['clinum']+" clientdo cmd \"Connect " + mod[4] + "\""
							kwargs['Broadcast'].broadcast("ClientExecScript "+player['clinum']+" clientdo cmd \"Connect " + mod[4] + "\"")
							break #break not return. we want to go to the next player not to leave the whole function and skip players
						else:
							break; #we will stop looking for matching mods for this player if found the matching one
				

	def updateModPlayers(self):
		for i in range (0, len(queue.modlist)-1):
			params = urllib.urlencode({'command':'countPlayersForMod','access_verifier':'ILoveJaredAndRoot', 'mod':queue.modlist[i][0]})
			conn = httplib.HTTPConnection("134.169.167.11")
			headers = {"Content-type": "application/x-www-form-urlencoded","Accept": "text/plain"}
			conn.request("POST", "/queue.php", params, headers)
			response = conn.getresponse()
			activePlayers = response.read().strip()
			queue.modlist[i][5] = activePlayers


	def updateModPlayersGameVars(self, **kwargs):
		i = 0
		for var_entry in queue.modVars:
			if ((len(queue.modlist)-1) < i):
				break
			kwargs['Broadcast'].broadcast("Set " + queue.modVars[i][5] + " " + queue.modlist[i][5])	
			i=i+1

	def onDisconnect(self, *args, **kwargs):
		cli = args[0]
		client = self.getPlayerByClientNum(cli)
		client['active'] = False
		self.leaveQueue(client['name'])
		
		i = 0
		for currentIndex in queue.playerlist:
			if ((len(queue.playerlist)-1) < i):
				break				
			if (queue.playerlist[i]['clinum'] == cli):
				del queue.playerlist[i]
				break;
			i=i+1
			


	def leaveQueue(self, args):
	#def leaveQueue(self, *args, **kwargs):
		name = args #its fine since its no an array its the var args which is a string which contains the player name
		params = urllib.urlencode({'command':'leaveMod','playername':name,'access_verifier':'ILoveJaredAndRoot'})
		conn = httplib.HTTPConnection("134.169.167.11")
		headers = {"Content-type": "application/x-www-form-urlencoded","Accept": "text/plain"}
		conn.request("POST", "/queue.php", params, headers)
		response = conn.getresponse()
		#playerqueue.remove(name)

		for client in queue.playerlist:
			if (client['name'] == name):
				client['mod'] = ''
				


	def joinQueue(self, args):		
	#def joinQueue(self, *args, **kwargs):	
		#playerqueue.remove(name)
		name = args[0]
		mod = args[1]
		params = urllib.urlencode({'command':'joinModQueue','playername':name,'mod':mod,'access_verifier':'ILoveJaredAndRoot'})
		conn = httplib.HTTPConnection("134.169.167.11")
		headers = {"Content-type": "application/x-www-form-urlencoded","Accept": "text/plain"}
		conn.request("POST", "/queue.php", params, headers)
		response = conn.getresponse()
		#playerqueue.append(name)

		for client in queue.playerlist:
			if (client['name'] == name):
				client['mod'] = mod

	def joinMod(self, args):		
	#def joinMod(self, *args, **kwargs):
		#playerqueue.remove(name)
		name = args[0]
		mod = args[1]
		params = urllib.urlencode({'command':'joinMod','playername':name,'mod':mod,'access_verifier':'ILoveJaredAndRoot'})
		conn = httplib.HTTPConnection("134.169.167.11")
		headers = {"Content-type": "application/x-www-form-urlencoded","Accept": "text/plain"}
		conn.request("POST", "/queue.php", params, headers)
		response = conn.getresponse()
		#playerqueue.append(name)
		
	def getMods(self):
		params = urllib.urlencode({'command':'getMods','access_verifier':'ILoveJaredAndRoot'})
		conn = httplib.HTTPConnection("134.169.167.11")
		headers = {"Content-type": "application/x-www-form-urlencoded","Accept": "text/plain"}
		conn.request("POST", "/queue.php", params, headers)
		response = conn.getresponse()
		data = response.read()
		rawmods = data.split("\n")
		queue.modlist = []

		for i in range (0, len(rawmods)-2):
			moddata = rawmods[i].split(";")	
			params = urllib.urlencode({'command':'countPlayersForMod','access_verifier':'ILoveJaredAndRoot', 'mod':moddata[0]})
			conn = httplib.HTTPConnection("134.169.167.11")
			headers = {"Content-type": "application/x-www-form-urlencoded","Accept": "text/plain"}
			conn.request("POST", "/queue.php", params, headers)
			response = conn.getresponse()
			activePlayers = response.read().strip()
			moddata.append(activePlayers)
			queue.modlist.append(moddata)	

	def getPlayerByName(self, name):
		for client in queue.playerlist:
			if (client['name'].lower() == name.lower()):
				return client

	def onConnect(self, *args, **kwargs):
		id = args[0]
		ip = args[2]
	
		for client in queue.playerlist:
			if (client['clinum'] == id):
				return
		
		queue.playerlist.append ({'clinum' : id,\
					 'acctid' : 0,\
					 'name' : 'X',\
					 'ip' : ip,\
					 'team' : 0,\
					 'sf' : 0,\
					 'active' : False,\
					 'level' : 0,\
					 'admin' : False,\
					 'value' : 0,\
					 'commander' : False,\
					 'mod' : "" })
	

	def onSetName(self, *args, **kwargs):
		cli = args[0]
		playername = args[1]
		client = self.getPlayerByClientNum(cli)
		client['name'] = playername


		if (int(queue.isModServer) == 1):
			localSetNameJoinlist = [playername, queue.isModServerCurrentMod]			
			#kwargs['Broadcast'].broadcast("SendMessage -1 IsmodServer in onSetName: Player " + str(playername) + " Joined Mod" + str(queue.isModServerCurrentMod))				
			self.joinMod(localSetNameJoinlist)
			#self.joinQueue(localSetNameJoinlist)

	def getPlayerByClientNum(self, cli):

		for client in queue.playerlist:
			if (client['clinum'] == cli):
				return client


	def onStartServer(self, *args, **kwargs):
		#Mod servers can not use the queue. They can just tell the queueserver that someone is playing on them
		kwargs['Broadcast'].broadcast("Set " + str(queue.isModServerGameVar) + " " + str(queue.isModServer))	
		queue.playerlist = []
		queue.modsLoaded = 1
		self.getMods()
		self.storeModsInGameVars(args, **kwargs)
		queue.resetUpdate = 0
		updatethread = threading.Thread(target=self.updatePlayerNumbers, args=(), kwargs=kwargs)
		updatethread.start()




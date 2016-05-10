/*
 * Surviveler game package
 * game state structure
 */

package game

import (
	log "github.com/Sirupsen/logrus"
	"server/game/entity"
	"server/game/messages"
	"server/game/protocol"
	"server/math"
)

// TODO: remove this soon...
const GAMESTATE_IS_A_MAP = false

/*
 * GameState is the structure that contains all the complete game state
 */
type GameState struct {
	players map[uint16]*entity.Player
}

func NewGameState() GameState {

	return GameState{
		players: make(map[uint16]*entity.Player),
	}
}

/*
 * pack transforms the current game state into a GameStateMsg,
 * ready to be sent to every connected client
 */
func (gs GameState) pack() (*protocol.Message, error) {

	// do not send nothing if we don't have players
	if len(gs.players) == 0 {
		return nil, nil
	}

	if GAMESTATE_IS_A_MAP {

		// fill the gamestatemsg
		var gsMsg messages.GameStateMsg
		gsMsg.Entities = make(map[uint16]messages.EntityStateMsg)
		for id, ent := range gs.players {

			snapshot := ent.GetSnapshot()

			gsMsg.Entities[id] = messages.EntityStateMsg{
				Tstamp: MakeTimestamp(),
				Xpos:   snapshot.CurPos[0],
				Ypos:   snapshot.CurPos[1],
				Action: messages.ActionMsg{
					ActionType:   messages.WalkingAction,
					TargetTstamp: snapshot.DestTstamp,
					Xpos:         snapshot.DestPos[0],
					Ypos:         snapshot.DestPos[1],
				},
			}
		}

		// wrap the specialized GameStateMsg into a generic Message
		msg, err := protocol.NewMessage(messages.GameStateId, gsMsg)
		if err != nil {
			log.WithField("err", err).Fatal("Couldn't pack Gamestate")
			return nil, err
		}
		log.WithField("msg", gsMsg).Debug("sent GamestateMsg")
		return msg, nil

	} else {

		// create a GameStateMsg from the game state
		for _, ent := range gs.players {

			snapshot := ent.GetSnapshot()

			gsMsg := messages.OldGameStateMsg{
				Tstamp: MakeTimestamp(),
				Xpos:   snapshot.CurPos[0],
				Ypos:   snapshot.CurPos[1],
				Action: messages.ActionMsg{
					ActionType:   messages.ActionType(messages.MoveId),
					TargetTstamp: snapshot.DestTstamp,
					Xpos:         snapshot.DestPos[0],
					Ypos:         snapshot.DestPos[1],
				},
			}

			// wrap the specialized GameStateMsg into a generic Message
			msg, err := protocol.NewMessage(messages.GameStateId, gsMsg)
			if err != nil {
				log.WithField("err", err).Fatal("Couldn't pack Gamestate")
				return nil, err
			}

			// exit after sending the first found entity state
			log.WithField("msg", gsMsg).Debug("sent GamestateMsg")
			return msg, nil
		}
	}
	return nil, nil
}

func (gs *GameState) onAddPlayer(msg interface{}, clientId uint16) error {
	// we have a new player, his id will be its unique connection id
	log.WithField("clientId", clientId).Info("we have a new player")
	gs.players[clientId] = entity.NewPlayer(0, 0, 2)
	return nil
}

func (gs *GameState) onDelPlayer(msg interface{}, clientId uint16) error {
	// one player less, remove him from the map
	log.WithField("clientId", clientId).Info("we have one less player")
	delete(gs.players, clientId)
	return nil
}

func (gs *GameState) onMovePlayer(msg interface{}, clientId uint16) error {

	move := msg.(messages.MoveMsg)
	log.WithFields(
		log.Fields{"clientId": clientId, "msg": move}).Info("handling a MoveMsg")

	if p, ok := gs.players[clientId]; ok {
		p.SetPos(math.Vec2{move.Xpos, move.Ypos})

		log.WithFields(
			log.Fields{"player": p, "clientId": clientId}).Info("MovePlayer")
	} else {
		log.WithField(
			"clientId", clientId).Panic("Player not found")
	}

	return nil
}

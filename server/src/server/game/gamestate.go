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

	// do not send nothing if no players yet
	if len(gs.players) == 0 {
		return nil, nil
	}

	// TODO: GameStateMsg will be represented by a list
	var ent0 *entity.Player
	ent0 = gs.players[0]

	// create a GameStateMsg from the game state
	gsMsg := messages.GameStateMsg{
		Tstamp: MakeTimestamp(),
		Xpos:   ent0.GetPos().X(),
		Ypos:   ent0.GetPos().Y(),
		Action: messages.ActionMsg{
			ActionType:   messages.MoveId,
			TargetTstamp: ent0.GetDestinationTimestamp(),
			Xpos:         ent0.GetDestination().X(),
			Ypos:         ent0.GetDestination().Y(),
		},
	}

	// wrap the specialized GameStateMsg into a generic Message
	msg, err := protocol.NewMessage(messages.GameStateId, gsMsg)
	if err != nil {
		log.WithField("err", err).Fatal("Couldn't pack Gamestate")
		return nil, err
	}

	return msg, nil
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
		p.SetDestination(math.Vec2{move.Xpos, move.Ypos})

		log.WithFields(
			log.Fields{"player": p, "clientId": clientId}).Info("MovePlayer")
	} else {
		log.WithField(
			"clientId", clientId).Panic("Player not found")
	}

	return nil
}

# -*- coding: utf-8 -*-
"""
football.routes.club_ops - Tài trợ, phòng truyền thống và thị trường chuyển nhượng.
"""
import json
import random
from flask import redirect, render_template, request, session, url_for

from football.models import Club, Player, db
from football.services.transfer_service import build_incoming_offers, build_transfer_market


def register_club_ops_routes(app):
    @app.route('/sponsorship', endpoint='sponsorship')
    def sponsorship():
        if 'club_id' not in session:
            return redirect(url_for('index'))
        club = db.session.get(Club, session['club_id'])
        if not club:
            return redirect(url_for('index'))
        message = session.pop('sponsor_message', None)
        return render_template('sponsorship.html', club=club, message=message)

    @app.route('/sign_sponsor', methods=['POST'], endpoint='sign_sponsor')
    def sign_sponsor():
        if 'club_id' not in session:
            return redirect(url_for('index'))
        club = db.session.get(Club, session['club_id'])
        if not club:
            return redirect(url_for('index'))
        sponsor_name = request.form.get('sponsor_name', 'VietinBank Sport')
        sponsor_weekly = request.form.get('sponsor_weekly', type=int) or 250000
        sponsor_bonus = request.form.get('sponsor_bonus', type=int) or 150000

        club.sponsor_name = sponsor_name
        club.sponsor_weekly = sponsor_weekly
        club.sponsor_bonus = sponsor_bonus
        db.session.commit()

        session['sponsor_message'] = f"🎉 Ký kết thành công hợp đồng tài trợ mới cùng {sponsor_name}! Trợ cấp: ${sponsor_weekly:,}/tuần."
        return redirect(url_for('sponsorship'))

    @app.route('/trophy_room', endpoint='trophy_room')
    def trophy_room():
        if 'club_id' not in session:
            return redirect(url_for('index'))
        club = db.session.get(Club, session['club_id'])
        if not club:
            return redirect(url_for('index'))
        try:
            trophies_list = json.loads(club.trophies or '[]')
        except Exception:
            trophies_list = []
        return render_template('trophy_room.html', club=club, trophies_list=trophies_list)

    @app.route('/transfer_market', methods=['GET', 'POST'], endpoint='transfer_market')
    def transfer_market():
        if 'club_id' not in session:
            return redirect(url_for('index'))
        club = db.session.get(Club, session['club_id'])
        if not club:
            return redirect(url_for('index'))

        squad_players = Player.query.filter_by(club_id=club.id).all()
        market = session.get('transfer_market')
        if market is None:
            market = build_transfer_market(club)
            session['transfer_market'] = market

        incoming_offers = session.get('incoming_offers')
        if incoming_offers is None:
            incoming_offers = build_incoming_offers(club, squad_players)
            session['incoming_offers'] = incoming_offers

        message = None
        error = None

        if request.method == 'POST':
            action = request.form.get('action', 'buy_now')

            if action == 'buy_now':
                candidate_id = request.form.get('candidate_id')
                candidate = next((item for item in market if item['id'] == candidate_id), None)
                if not candidate:
                    error = 'Cầu thủ này không còn trên thị trường.'
                elif club.money < candidate['price']:
                    error = f'Ngân sách không đủ ${candidate["price"]:,} để mua cầu thủ này.'
                else:
                    player = Player(
                        name=candidate['name'], position=candidate['position'],
                        attack=candidate['attack'], defense=candidate['defense'],
                        speed=candidate['speed'], overall=candidate['overall'],
                        stamina=100.0, preferred_positions=json.dumps([candidate['position']]),
                        club_id=club.id
                    )
                    db.session.add(player)
                    club.money -= candidate['price']
                    market.remove(candidate)
                    session['transfer_market'] = market
                    session.modified = True
                    db.session.commit()
                    message = f"✅ Đã ký hợp đồng thành công với {player.name}!"

            elif action == 'negotiate_bid':
                candidate_id = request.form.get('candidate_id')
                discount = float(request.form.get('bid_discount', 1.0))
                candidate = next((item for item in market if item['id'] == candidate_id), None)
                if not candidate:
                    error = 'Cầu thủ này không còn trên thị trường.'
                else:
                    bid_price = int(candidate['price'] * discount)
                    if club.money < bid_price:
                        error = f'Ngân sách không đủ ${bid_price:,} cho mức giá đề xuất này.'
                    else:
                        success_rate = 0.6 if discount <= 0.85 else (0.85 if discount <= 0.90 else 0.98)
                        if random.random() <= success_rate:
                            player = Player(
                                name=candidate['name'], position=candidate['position'],
                                attack=candidate['attack'], defense=candidate['defense'],
                                speed=candidate['speed'], overall=candidate['overall'],
                                stamina=100.0, preferred_positions=json.dumps([candidate['position']]),
                                club_id=club.id
                            )
                            db.session.add(player)
                            club.money -= bid_price
                            market.remove(candidate)
                            session['transfer_market'] = market
                            session.modified = True
                            db.session.commit()
                            saved = candidate['price'] - bid_price
                            message = f"🎉 Đàm phán thành công! CLB đối tác đồng ý bán {player.name} với giá ${bid_price:,} (Tiết kiệm được ${saved:,})!"
                        else:
                            error = f"❌ CLB đối tác đã từ chối lời đề nghị trả giá rẻ hơn {int((1 - discount) * 100)}% của bạn!"

            elif action == 'sell_player':
                player_id = request.form.get('player_id', type=int)
                p = db.session.get(Player, player_id)
                if len(squad_players) <= 11:
                    error = 'Không thể bán vì đội hình tối thiểu cần 11 cầu thủ!'
                elif p and p.club_id == club.id:
                    sale_value = int(p.overall * 65000)
                    club.money += sale_value
                    p_name = p.name
                    db.session.delete(p)
                    db.session.commit()
                    squad_players = Player.query.filter_by(club_id=club.id).all()
                    message = f"📤 Đã bán {p_name} và thu về +${sale_value:,} vào ngân sách!"

            elif action == 'accept_offer':
                offer_id = request.form.get('offer_id')
                offer = next((o for o in incoming_offers if o['id'] == offer_id), None)
                if offer:
                    p = db.session.get(Player, offer['player_id'])
                    if p and p.club_id == club.id and len(squad_players) > 11:
                        club.money += offer['offer_price']
                        db.session.delete(p)
                        incoming_offers.remove(offer)
                        session['incoming_offers'] = incoming_offers
                        session.modified = True
                        db.session.commit()
                        squad_players = Player.query.filter_by(club_id=club.id).all()
                        message = f"🤝 Đã hoàn tất chuyển nhượng! {p.name} gia nhập {offer['club_name']} với giá ${offer['offer_price']:,}!"
                    else:
                        error = 'Không thể bán cầu thủ này hoặc đội hình không đủ số lượng tối thiểu!'

            elif action == 'reject_offer':
                offer_id = request.form.get('offer_id')
                incoming_offers = [o for o in incoming_offers if o['id'] != offer_id]
                session['incoming_offers'] = incoming_offers
                session.modified = True
                message = "Đã từ chối lời đề nghị chuyển nhượng."

        return render_template('transfer_market.html', club=club, candidates=market,
                               squad_players=squad_players, incoming_offers=incoming_offers,
                               message=message, error=error)

from threading import Timer


def test_run(bot, action):
    action.end = lambda *a: bot.stop()
    assert bot.running, 'Bot not running'
    bot.add_action(action)
    bot.run()
    assert action.count > 0, 'Did not run action'


def test_stop(bot, action):
    bot.add_action(action)
    Timer(1e-3, bot.stop).start()
    bot.run()
    assert not bot.running, 'Bot running after stop'
    assert action.count > 0, 'Did not run action'


def test_restart_action(bot, action):
    _id = bot.add_action(action)
    bot.start()
    bot.wait(_id)
    assert action.done, 'Action not complete'
    bot.start_action(_id)
    bot.wait(_id)
    bot.close()
    assert action.count > 5, 'Did not run action more than once'


def test_run_multiple_actions():
    pass


def test_add_action_while_running():
    pass


def test_stop_action_while_running():
    pass

